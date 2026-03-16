#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const cwd = process.cwd();

const teamsFileArg = process.argv[2] || path.join('src/data', 'teams2026.json');
const targetFileArg = process.argv[3] || path.join('src/data', 'kpOvrStats2026.json');
const upsetFileArg = process.argv[4] || path.join('src/data', 'upsetData.json');

const teamsFilePath = path.resolve(cwd, teamsFileArg);
const targetFilePath = path.resolve(cwd, targetFileArg);
const upsetFilePath = path.resolve(cwd, upsetFileArg);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

async function main() {
  const teamNameModulePath = path.resolve(__dirname, 'teamName.mjs');
  const teamNameModuleUrl = pathToFileURL(teamNameModulePath).href;
  const { normalizeTeamName } = await import(teamNameModuleUrl);

  if (typeof normalizeTeamName !== 'function') {
    throw new Error('Expected teamName.mjs to export normalizeTeamName(name).');
  }

  if (!fs.existsSync(teamsFilePath)) {
    console.error(`Teams file not found: ${teamsFilePath}`);
    process.exit(1);
  }

  if (!fs.existsSync(targetFilePath)) {
    console.error(`Target file not found: ${targetFilePath}`);
    process.exit(1);
  }

  if (!fs.existsSync(upsetFilePath)) {
    console.error(`Upset data file not found: ${upsetFilePath}`);
    process.exit(1);
  }

  const teams = readJson(teamsFilePath);
  const target = readJson(targetFilePath);
  const upsetData = readJson(upsetFilePath);

  if (!Array.isArray(teams)) {
    console.error('Expected teams file to be a JSON array of team names.');
    process.exit(1);
  }

  if (!target || Array.isArray(target) || typeof target !== 'object') {
    console.error('Expected target file to be a JSON object keyed by team name.');
    process.exit(1);
  }

  if (!upsetData || Array.isArray(upsetData) || typeof upsetData !== 'object') {
    console.error('Expected upset data file to be a JSON object.');
    process.exit(1);
  }

  if (
    !upsetData.matchups ||
    Array.isArray(upsetData.matchups) ||
    typeof upsetData.matchups !== 'object'
  ) {
    console.error('Expected upset data file to contain a top-level "matchups" object.');
    process.exit(1);
  }

  if (
    !upsetData.regions ||
    Array.isArray(upsetData.regions) ||
    typeof upsetData.regions !== 'object'
  ) {
    console.error('Expected upset data file to contain a top-level "regions" object.');
    process.exit(1);
  }

  const normalizedValidTeams = new Set(
    teams.map((teamName) => normalizeTeamName(String(teamName))),
  );
  const beforeCount = Object.keys(target).length;
  const removedTeams = [];

  const filtered = {};
  for (const [teamName, value] of Object.entries(target)) {
    if (normalizedValidTeams.has(normalizeTeamName(teamName))) {
      filtered[teamName] = value;
    } else {
      removedTeams.push(teamName);
    }
  }

  writeJson(targetFilePath, filtered);

  console.log(`Cleaned ${targetFileArg}`);
  console.log(`Before: ${beforeCount}`);
  console.log(`After: ${Object.keys(filtered).length}`);
  console.log(`Removed: ${removedTeams.length}`);

  if (removedTeams.length > 0) {
    console.log('\nRemoved team names:');
    for (const teamName of removedTeams.sort()) {
      console.log(`- ${teamName}`);
    }
  }

  const upsetBeforeCount = Object.keys(upsetData.matchups).length;
  const removedUpsetMatchups = [];
  const cleanedMatchups = {};

  for (const [matchupId, matchupValue] of Object.entries(upsetData.matchups)) {
    const [teamA, teamB] = String(matchupId).split('_');
    if (
      !teamA ||
      !teamB ||
      !normalizedValidTeams.has(normalizeTeamName(teamA)) ||
      !normalizedValidTeams.has(normalizeTeamName(teamB))
    ) {
      removedUpsetMatchups.push(matchupId);
      continue;
    }
    cleanedMatchups[matchupId] = matchupValue;
  }

  const validMatchupIds = new Set(Object.keys(cleanedMatchups));
  let removedRegionReferences = 0;
  const cleanedRegions = {};

  for (const [region, regionMatchups] of Object.entries(upsetData.regions)) {
    if (!Array.isArray(regionMatchups)) {
      cleanedRegions[region] = regionMatchups;
      continue;
    }

    const filteredRegionMatchups = regionMatchups.filter((matchupId) => {
      const keep = validMatchupIds.has(matchupId);
      if (!keep) {
        removedRegionReferences += 1;
      }
      return keep;
    });

    cleanedRegions[region] = filteredRegionMatchups;
  }

  upsetData.matchups = cleanedMatchups;
  upsetData.regions = cleanedRegions;

  writeJson(upsetFilePath, upsetData);

  console.log(`\nCleaned ${upsetFileArg}`);
  console.log(`Matchups before: ${upsetBeforeCount}`);
  console.log(`Matchups after: ${Object.keys(cleanedMatchups).length}`);
  console.log(`Matchups removed: ${removedUpsetMatchups.length}`);
  console.log(`Region matchup refs removed: ${removedRegionReferences}`);

  if (removedUpsetMatchups.length > 0) {
    console.log('\nRemoved upset matchups:');
    for (const matchupId of removedUpsetMatchups.sort()) {
      console.log(`- ${matchupId}`);
    }
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
