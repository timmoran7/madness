import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(process.cwd());
const TEAMS_PATH = resolve(ROOT, "src/data/teams2026.json");
const LOGOS_PATH = resolve(ROOT, "src/data/team_logos.json");
const OUTPUT_PATH = resolve(ROOT, "src/data/teamLogoUrls.json");

const teams = JSON.parse(readFileSync(TEAMS_PATH, "utf8"));
const logos = JSON.parse(readFileSync(LOGOS_PATH, "utf8"));

// Known aliases where school naming differs significantly between datasets.
const MANUAL_OVERRIDES = {
  "Alabama St": "Alabama State Hornets",
  "Colorado St": "Colorado State Rams",
  Connecticut: "UConn Huskies",
  "Iowa St": "Iowa State Cyclones",
  LIU: "Long Island University Sharks",
  "Miami FL": "Miami Hurricanes",
  "Michigan St": "Michigan State Spartans",
  Mississippi: "Ole Miss Rebels",
  "Mississippi St": "Mississippi State Bulldogs",
  "Mount St Marys": "Mount St. Mary's Mountaineers",
  "NC State": "NC State Wolfpack",
  "Nebraska Omaha": "Omaha Mavericks",
  "North Dakota St": "North Dakota State Bison",
  "Norfolk St": "Norfolk State Spartans",
  "Ohio St": "Ohio State Buckeyes",
  "Saint Francis": "Saint Francis Red Flash",
  "Saint Marys": "Saint Mary's Gaels",
  "San Diego St": "San Diego State Aztecs",
  SIUE: "SIU Edwardsville Cougars",
  "St Johns": "St. John's Red Storm",
  "Tennessee St": "Tennessee State Tigers",
  "Texas Tech": "Texas Tech Red Raiders",
  "UC San Diego": "UC San Diego Tritons",
  "UNC Wilmington": "UNC Wilmington Seahawks",
  "Utah St": "Utah State Aggies",
  "Wright St": "Wright State Raiders",
};

const TOKEN_ALIASES = {
  fl: "florida",
  liu: "long island university",
  miss: "mississippi",
  "ole miss": "mississippi",
  siue: "siu edwardsville",
  st: "state",
  uconn: "connecticut",
};

// Mascot and descriptor words that can appear in ESPN team names without changing school identity.
const IGNORABLE_EXTRA_TOKENS = new Set([
  "aggies",
  "anteaters",
  "aztecs",
  "badgers",
  "bears",
  "beavers",
  "billikens",
  "bison",
  "blazers",
  "blue",
  "bluejays",
  "boilermakers",
  "braves",
  "broncos",
  "bruins",
  "buckeyes",
  "bulldogs",
  "cavaliers",
  "catamounts",
  "cougars",
  "crimson",
  "cyclones",
  "devils",
  "dons",
  "eagles",
  "fighting",
  "flash",
  "frogs",
  "gaels",
  "gators",
  "golden",
  "green",
  "hawks",
  "heels",
  "hoosiers",
  "horned",
  "hurricanes",
  "huskies",
  "illini",
  "jaguars",
  "jayhawks",
  "knights",
  "lions",
  "lobos",
  "longhorns",
  "mavericks",
  "mountaineers",
  "mustangs",
  "owls",
  "panthers",
  "peacocks",
  "pirates",
  "raiders",
  "ramblers",
  "rams",
  "rebels",
  "red",
  "revolutionaries",
  "roos",
  "runnin",
  "seahawks",
  "spartans",
  "spiders",
  "storm",
  "sycamores",
  "tar",
  "terriers",
  "tigers",
  "trojans",
  "utes",
  "volunteers",
  "wildcats",
  "wolfpack",
  "wolverines",
  "wolves",
]);

function normalize(text) {
  const value = text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[.'-]/g, " ")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const rawTokens = value.split(" ").filter(Boolean);
  const normalizedTokens = [];

  for (let index = 0; index < rawTokens.length; index += 1) {
    let token = rawTokens[index];

    // "St Johns" and similar schools are saint-based, not state-based.
    if (token === "st" && ["johns", "marys", "francis"].includes(rawTokens[index + 1])) {
      token = "saint";
    } else {
      token = TOKEN_ALIASES[token] ?? token;
    }

    normalizedTokens.push(token);
  }

  return normalizedTokens;
}

function scoreCandidate(teamName, logoName) {
  const teamTokens = new Set(normalize(teamName));
  const logoTokens = new Set(normalize(logoName));

  const missingTeamTokens = [...teamTokens].filter((token) => !logoTokens.has(token));
  if (missingTeamTokens.length > 0) {
    return -1;
  }

  // Start with a high score, then penalize extra school-distinguishing words.
  let score = 1;
  const extraLogoTokens = [...logoTokens].filter((token) => !teamTokens.has(token));

  for (const token of extraLogoTokens) {
    score -= IGNORABLE_EXTRA_TOKENS.has(token) ? 0.03 : 0.3;
  }

  const teamPhrase = normalize(teamName).join(" ");
  const logoPhrase = normalize(logoName).join(" ");
  if (logoPhrase.includes(teamPhrase)) {
    score += 0.08;
  }

  return score;
}

function findBestLogoName(teamName) {
  const logoNames = Object.keys(logos);
  let bestName = "";
  let bestScore = -1;

  for (const logoName of logoNames) {
    const currentScore = scoreCandidate(teamName, logoName);
    if (currentScore > bestScore) {
      bestName = logoName;
      bestScore = currentScore;
    }
  }

  return { bestName, bestScore };
}

const mapping = {};
const unresolved = [];

for (const teamName of teams) {
  const forcedLogoName = MANUAL_OVERRIDES[teamName];
  if (forcedLogoName) {
    mapping[teamName] = logos[forcedLogoName]?.logo ?? "";
    continue;
  }

  const { bestName, bestScore } = findBestLogoName(teamName);

  if (bestScore >= 0.5 && logos[bestName]?.logo) {
    mapping[teamName] = logos[bestName].logo;
  } else {
    unresolved.push({
      team: teamName,
      bestCandidate: bestName,
      score: Number(bestScore.toFixed(3)),
    });
  }
}

const sortedMapping = Object.fromEntries(
  Object.entries(mapping).sort(([a], [b]) => a.localeCompare(b)),
);

writeFileSync(OUTPUT_PATH, `${JSON.stringify(sortedMapping, null, 2)}\n`, "utf8");

if (unresolved.length > 0) {
  console.warn("Unresolved teams:");
  for (const item of unresolved) {
    console.warn(`${item.team} => ${item.bestCandidate} (${item.score})`);
  }
} else {
  console.log("All teams resolved.");
}

console.log(`Wrote ${Object.keys(sortedMapping).length} team logo URLs to ${OUTPUT_PATH}.`);
