const GREEN: [number, number, number] = [144, 235, 94];
const GRAY: [number, number, number] = [255, 255, 255];
const RED: [number, number, number] = [196, 79, 57];
const LIGHT_BLUE: [number, number, number] = [220, 237, 245];
const DARK_BLUE: [number, number, number] = [100, 160, 210];

const MIN_RANK = 1;
const MAX_RANK = 365;
const MID_RANK = Math.round((MIN_RANK + MAX_RANK) / 2);

const BLUE_GRADIENT_LABELS = new Set([
  "Tempo",
  "Minutes Continuity",
  "Bench Minutes",
  "D-1 Experience",
]);

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
    return "rgb(255,255,255)";
  }

  const clampedRank = clamp(rank, MIN_RANK, MAX_RANK);

  if (clampedRank <= MID_RANK) {
    const t = (clampedRank - MIN_RANK) / (MID_RANK - MIN_RANK);
    return interpolateRgb(GREEN, GRAY, t);
  }

  const t = (clampedRank - MID_RANK) / (MAX_RANK - MID_RANK);
  return interpolateRgb(GRAY, RED, t);
}

function getTempoColor(rankValue: string): string {
  const rank = Number.parseFloat(rankValue);
  if (!Number.isFinite(rank)) {
    return "rgb(255,255,255)";
  }

  const t =
    (clamp(rank, MIN_RANK, MAX_RANK) - MIN_RANK) / (MAX_RANK - MIN_RANK);
  return interpolateRgb(DARK_BLUE, LIGHT_BLUE, t);
}

export function getStatRankColor(label: string, rankValue: string): string {
  if (BLUE_GRADIENT_LABELS.has(label)) {
    return getTempoColor(rankValue);
  }

  return getRankColor(rankValue);
}
