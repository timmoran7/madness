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
const ROUND_OF_64_SEED_PAIRS = [
  [1, 16],
  [8, 9],
  [5, 12],
  [4, 13],
  [6, 11],
  [3, 14],
  [7, 10],
  [2, 15],
];

for (const [region, regionMatchups] of Object.entries(regions)) {
  if (regionMatchups.length < 8 || regionMatchups.length > 10) {
    throw new Error(
      `Expected 8, 9, or 10 matchups in region ${region}, received ${regionMatchups.length}.`,
    );
  }

  let nextSeedPairIndex = 0;
  let previousFirstTeamRaw = null;
  let previousWasDuplicate = false;

  regionMatchups.forEach((matchup, matchupIndex) => {
    const [highSeedTeamRaw, lowSeedTeamRaw] = matchup.split("_");
    if (!highSeedTeamRaw || !lowSeedTeamRaw) {
      throw new Error(`Invalid matchup format in region ${region}: ${matchup}`);
    }

    const sameFirstTeamAsPrevious =
      previousFirstTeamRaw !== null &&
      normalizeTeamName(highSeedTeamRaw) === normalizeTeamName(previousFirstTeamRaw);

    if (sameFirstTeamAsPrevious && previousWasDuplicate) {
      throw new Error(
        `Unexpected third consecutive matchup with first team ${highSeedTeamRaw} in region ${region}.`,
      );
    }

    const seedPairIndex = sameFirstTeamAsPrevious
      ? nextSeedPairIndex - 1
      : nextSeedPairIndex;

    if (seedPairIndex < 0 || seedPairIndex >= ROUND_OF_64_SEED_PAIRS.length) {
      throw new Error(
        `Could not map matchup ${matchup} at index ${matchupIndex} to a valid seed pair in region ${region}.`,
      );
    }

    const [highSeed, lowSeed] = ROUND_OF_64_SEED_PAIRS[seedPairIndex];

    if (!sameFirstTeamAsPrevious) {
      nextSeedPairIndex += 1;
    }

    previousFirstTeamRaw = highSeedTeamRaw;
    previousWasDuplicate = sameFirstTeamAsPrevious;

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

  if (nextSeedPairIndex !== ROUND_OF_64_SEED_PAIRS.length) {
    throw new Error(
      `Region ${region} did not resolve to all 8 round-of-64 seed slots. Resolved ${nextSeedPairIndex}.`,
    );
  }
}

for (const [teamName, seed] of seedAssignments.entries()) {
  kpStats[teamName].seed = seed;
}

writeFileSync(kpStatsPath, `${JSON.stringify(kpStats, null, 2)}\n`, "utf8");

console.log(`Assigned seeds for ${seedAssignments.size} teams in ${kpStatsPath}`);
