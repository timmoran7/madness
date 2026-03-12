import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const upsetDataPath = resolve("src/data/upsetData.json");
const kpStatsPath = resolve("src/data/kpOvrStats2026.json");

const upsetData = JSON.parse(readFileSync(upsetDataPath, "utf8"));
const kpStats = JSON.parse(readFileSync(kpStatsPath, "utf8"));

const normalizeTeamName = (name) =>
  name
    .toLowerCase()
    .replace(/\./g, "")
    .replace(/'/g, "")
    .replace(/&/g, "and")
    .replace(/\s+/g, " ")
    .trim();

const kpKeysByNormalizedName = new Map(
  Object.keys(kpStats).map((teamName) => [normalizeTeamName(teamName), teamName]),
);

const resolveKpTeamKey = (teamName) => {
  if (teamName in kpStats) {
    return teamName;
  }

  const normalized = normalizeTeamName(teamName);
  return kpKeysByNormalizedName.get(normalized) ?? null;
};

const seedAssignments = new Map();
const regions = upsetData.regions ?? {};

for (const [region, regionMatchups] of Object.entries(regions)) {
  if (!Array.isArray(regionMatchups) || regionMatchups.length !== 8) {
    throw new Error(`Region ${region} does not have exactly 8 first-round matchups.`);
  }

  regionMatchups.forEach((matchup, matchupIndex) => {
    const [highSeedTeamRaw, lowSeedTeamRaw] = matchup.split("_");
    if (!highSeedTeamRaw || !lowSeedTeamRaw) {
      throw new Error(`Invalid matchup format in region ${region}: ${matchup}`);
    }

    const highSeed = matchupIndex + 1;
    const lowSeed = 17 - highSeed;

    const highSeedTeam = resolveKpTeamKey(highSeedTeamRaw);
    const lowSeedTeam = resolveKpTeamKey(lowSeedTeamRaw);

    if (!highSeedTeam || !lowSeedTeam) {
      throw new Error(
        `Could not resolve matchup teams for ${matchup} in region ${region}.`,
      );
    }

    seedAssignments.set(highSeedTeam, highSeed);
    seedAssignments.set(lowSeedTeam, lowSeed);
  });
}

for (const [teamName, seed] of seedAssignments.entries()) {
  kpStats[teamName].seed = seed;
}

writeFileSync(kpStatsPath, `${JSON.stringify(kpStats, null, 2)}\n`, "utf8");

console.log(`Assigned seeds for ${seedAssignments.size} teams in ${kpStatsPath}`);
