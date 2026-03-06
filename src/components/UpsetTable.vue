<script setup lang="ts">
interface UpsetData {
  columns: string[];
  values: string[];
}

defineProps<{
  data: UpsetData;
}>();

const GREEN: [number, number, number] = [144, 235, 94];
const GRAY: [number, number, number] = [255, 255, 255];
const RED: [number, number, number] = [196, 79, 57];

const MIN_SCORE = 0;
const MID_SCORE = 5;
const MAX_SCORE = 10;

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

function getUpsetColor(value: string): string {
  const score = Number.parseFloat(value);
  if (!Number.isFinite(score)) {
    return 'rgb(255,255,255)';
  }

  const clampedScore = clamp(score, MIN_SCORE, MAX_SCORE);

  if (clampedScore <= MID_SCORE) {
    const t = (clampedScore - MIN_SCORE) / (MID_SCORE - MIN_SCORE);
    return interpolateRgb(RED, GRAY, t);
  }

  const t = (clampedScore - MID_SCORE) / (MAX_SCORE - MID_SCORE);
  return interpolateRgb(GRAY, GREEN, t);
}
</script>

<template>
  <div class="container">
    <h2 class="text-center">Upset Factors</h2>
    <h6 class="text-center"><em>Upset Correlation out of 10</em></h6>
    <div class="table-responsive">
      <table class="table table-bordered table-striped">
        <thead>
          <tr class="text-center">
            <th 
              v-for="(column, index) in data.columns" 
              :key="index"
              style="background-color: #ffffff; color: #000000"
            >
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr class="text-center">
            <td 
              v-for="(value, index) in data.values" 
              :key="index"
              :style="{ backgroundColor: getUpsetColor(value) }"
            >
              {{ value }}
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
</style>
