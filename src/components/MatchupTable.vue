<script setup lang="ts">
interface Stat {
  value: string;
}

interface Team {
  name: string;
  stats: Stat[];
}

interface MatchupData {
  columns: string[];
  teams: Team[];
}

defineProps<{
  data: MatchupData;
}>();

const GREEN: [number, number, number] = [144, 235, 94];
const GRAY: [number, number, number] = [255, 255, 255];
const RED: [number, number, number] = [196, 79, 57];

const MIN_RANK = 1;
const MAX_RANK = 365;
const MID_RANK = Math.round((MIN_RANK + MAX_RANK) / 2);

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function interpolateChannel(start: number, end: number, t: number): number {
  return Math.round(start + (end - start) * t);
}

function interpolateRgb(
  start: [number, number, number],
  end: [number, number, number],
  t: number,
): string {
  return `rgb(${interpolateChannel(start[0], end[0], t)},${interpolateChannel(start[1], end[1], t)},${interpolateChannel(start[2], end[2], t)})`;
}

function getRankColor(rankValue: string): string {
  const rank = Number.parseFloat(rankValue);
  if (!Number.isFinite(rank)) {
    return 'rgb(255,255,255)';
  }

  const clampedRank = clamp(rank, MIN_RANK, MAX_RANK);

  if (clampedRank <= MID_RANK) {
    const t = (clampedRank - MIN_RANK) / (MID_RANK - MIN_RANK);
    return interpolateRgb(GREEN, GRAY, t);
  }

  const t = (clampedRank - MID_RANK) / (MAX_RANK - MID_RANK);
  return interpolateRgb(GRAY, RED, t);
}
</script>

<template>
  <div class="container">
    <h2 class="text-center">All Stats</h2> 
    <h6 class="text-center"><em>Rank of all 364 NCAAB D1 teams</em></h6>
    <div class="table-responsive">
      <table class="table table-bordered table-striped">
        <thead class="text-center">
          <tr>
            <th class="team-name">Team</th>
            <th v-for="(column, index) in data.columns" :key="index">{{ column }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(team, teamIndex) in data.teams" :key="teamIndex" class="text-center">
            <td class="team-name">{{ team.name }}</td>
            <td 
              v-for="(stat, statIndex) in team.stats" 
              :key="statIndex"
              :style="{ backgroundColor: getRankColor(stat.value) }"
            >
              {{ stat.value }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table { 
  background-color: white; 
}

th, td { 
  text-align: center; 
}

th.team-name { 
  background-color: #888888; 
  color: white; 
}
</style>
