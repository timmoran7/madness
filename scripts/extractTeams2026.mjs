import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const inputPath = resolve("src/data/kpOvrStats2026.json");
const outputPath = resolve("src/data/teams2026.json");

const data = JSON.parse(readFileSync(inputPath, "utf8"));
const teams = Object.keys(data);

writeFileSync(outputPath, `${JSON.stringify(teams, null, 2)}\n`, "utf8");

console.log(`Wrote ${teams.length} teams to ${outputPath}`);