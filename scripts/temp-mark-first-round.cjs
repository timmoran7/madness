#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const cwd = process.cwd();
const targetFileArg = process.argv[2] || path.join('src/data', 'upsetData.json');
const targetFilePath = path.resolve(cwd, targetFileArg);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

if (!fs.existsSync(targetFilePath)) {
  console.error(`Target file not found: ${targetFilePath}`);
  process.exit(1);
}

const data = readJson(targetFilePath);

if (!data || typeof data !== 'object' || Array.isArray(data)) {
  console.error('Expected target file to be a JSON object.');
  process.exit(1);
}

if (!data.matchups || typeof data.matchups !== 'object' || Array.isArray(data.matchups)) {
  console.error('Expected target file to contain a top-level "matchups" object.');
  process.exit(1);
}

if (!data.regions || typeof data.regions !== 'object' || Array.isArray(data.regions)) {
  console.error('Expected target file to contain a top-level "regions" object.');
  process.exit(1);
}

const firstRoundIds = new Set();
for (const ids of Object.values(data.regions)) {
  if (!Array.isArray(ids)) {
    continue;
  }
  for (const matchupId of ids) {
    if (typeof matchupId === 'string') {
      firstRoundIds.add(matchupId);
    }
  }
}

let yesCount = 0;
let noCount = 0;

for (const [matchupId, matchupData] of Object.entries(data.matchups)) {
  if (!matchupData || typeof matchupData !== 'object' || Array.isArray(matchupData)) {
    continue;
  }

  if (firstRoundIds.has(matchupId)) {
    matchupData.firstRound = 'yes';
    yesCount += 1;
  } else {
    matchupData.firstRound = 'no';
    noCount += 1;
  }
}

writeJson(targetFilePath, data);

console.log(`Updated ${targetFileArg}`);
console.log(`Marked firstRound: yes -> ${yesCount}`);
console.log(`Marked firstRound: no  -> ${noCount}`);
console.log(`Region source IDs found: ${firstRoundIds.size}`);
