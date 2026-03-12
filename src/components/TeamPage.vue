<script setup lang="ts">
import { computed, toRefs } from "vue";
import { useRoute, useRouter } from "vue-router";
import QuadCard from "@/components/QuadCard.vue";
import { getStatRankColor } from "@/utils/rankGradient";

interface TeamPageStats {
  rankRatingStats: TeamPageStatRow[];
  overallRank: string;
  record: string;
  netRank: string;
}

interface TeamStatDetail {
  rank: string;
  value: string;
}

interface TeamPageStatRow extends TeamStatDetail {
  label: string;
}

interface QuadBucket {
  record: string;
  games: string[];
}

interface TeamQuadResults {
  q1: QuadBucket;
  q2: QuadBucket;
  q3: QuadBucket;
  q4: QuadBucket;
}

interface TeamGameRow {
  date: string;
  opponentRank: string;
  opponent: string;
  result: string;
  location: string;
  record: string;
  conferenceRecord: string;
}

const router = useRouter();
const route = useRoute();

const goBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }

  router.push({
    name: "matchup",
    query: {
      region:
        typeof route.query.region === "string" ? route.query.region : undefined,
      matchup:
        typeof route.query.matchup === "string"
          ? route.query.matchup
          : undefined,
    },
  });
};

const isWin = (game: string): boolean => {
  const match = game.match(/^(\d+)-(\d+)/);
  if (!match) return false;
  return parseInt(match[1], 10) > parseInt(match[2], 10);
};

const getOrdinalSuffix = (rank: string) => {
  const numericRank = Number.parseInt(rank.replace(/\D/g, ""), 10);

  if (Number.isNaN(numericRank)) {
    return "";
  }

  const lastTwoDigits = numericRank % 100;
  if (lastTwoDigits >= 11 && lastTwoDigits <= 13) {
    return "th";
  }

  const lastDigit = numericRank % 10;
  if (lastDigit === 1) {
    return "st";
  }

  if (lastDigit === 2) {
    return "nd";
  }

  if (lastDigit === 3) {
    return "rd";
  }

  return "th";
};

const formatResult = (result: string): string => {
  return result
    .replace(/\s*,\s*/g, ", ")
    .replace(/\s+/g, " ")
    .trim();
};

const isResultWin = (result: string): boolean => {
  return formatResult(result).toUpperCase().startsWith("W,");
};

const formatScoreOnly = (result: string): string => {
  const cleaned = formatResult(result);
  const scoreMatch = cleaned.match(/(\d+\s*-\s*\d+\*?)/);
  if (!scoreMatch) {
    return cleaned;
  }

  return scoreMatch[1].replace(/\s+/g, "");
};

const formatGameDate = (date: string): string => {
  const match = date.match(/^[A-Za-z]{3}\s+([A-Za-z]{3})\s+(\d{1,2})$/);
  if (!match) {
    return date;
  }

  const monthMap: Record<string, number> = {
    Jan: 1,
    Feb: 2,
    Mar: 3,
    Apr: 4,
    May: 5,
    Jun: 6,
    Jul: 7,
    Aug: 8,
    Sep: 9,
    Oct: 10,
    Nov: 11,
    Dec: 12,
  };

  const month = monthMap[match[1]];
  if (!month) {
    return date;
  }

  return `${month}/${Number.parseInt(match[2], 10)}`;
};

const formatOpponentWithRank = (opponent: string, rank: string): string => {
  const parsedRank = Number.parseInt(rank, 10);
  if (Number.isNaN(parsedRank) || parsedRank <= 0) {
    return opponent;
  }

  return `${opponent} <b>(${parsedRank})</b>`;
};

const props = defineProps<{
  teamName: string;
  teamLogo: string;
  gameLog: TeamGameRow[];
  stats: TeamPageStats;
  quads: TeamQuadResults;
}>();

const { teamName, teamLogo, gameLog, stats, quads } = toRefs(props);

const quadCards = computed(() => [
  { label: "Q1", quad: quads.value.q1 },
  { label: "Q2", quad: quads.value.q2 },
  { label: "Q3", quad: quads.value.q3 },
  { label: "Q4", quad: quads.value.q4 },
]);

const gameLogStats = ["SOS Overall", "SOS Non-conference"];
const gridStats = computed(() =>
  stats.value.rankRatingStats.filter(
    (stat) => !gameLogStats.includes(stat.label),
  ),
);
const sosOverallRank = computed(
  () =>
    stats.value.rankRatingStats.find(
      (stat) => stat.label === gameLogStats[0],
    )?.rank ?? "-",
);
const sosNonConferenceRank = computed(
  () =>
    stats.value.rankRatingStats.find(
      (stat) => stat.label === gameLogStats[1],
    )?.rank ?? "-",
);
</script>

<template>
  <section
    class="team-page border border-secondary rounded bg-light mt-4 p-3 position-relative"
  >
    <button class="btn btn-outline-secondary back-button" @click="goBack">
      Back
    </button>

    <div class="team-layout">
      <div class="team-left">
        <div class="team-hero mb-3">
          <img :src="teamLogo" :alt="teamName" class="team-logo" />
          <div>
            <div class="team-header">
              <h2>{{ teamName }}</h2>
              <p class="record-line">
                <span class="extra-bold">{{ stats.record }}</span> |
                <span class="extra-bold">{{ stats.overallRank }}</span
                ><sup>{{ getOrdinalSuffix(stats.overallRank) }}</sup> KenPom,
                <span class="extra-bold">{{ stats.netRank }}</span>
                <sup>{{ getOrdinalSuffix(stats.netRank) }}</sup> NET
              </p>
            </div>
          </div>
        </div>

        <p style="font-size: 14px">
          <em><b>Ranks of 365 D1 teams</b></em>
        </p>
        <div class="stats-grid mb-4">
          <article
            v-for="stat in gridStats"
            :key="stat.label"
            class="stat-card"
          >
            <p class="label">{{ stat.label }}</p>
            <p class="value">
              <span
                class="rank-chip"
                :style="{ backgroundColor: getStatRankColor(stat.label, stat.rank) }"
                >{{ stat.rank }}</span
              >
              <span class="value-detail">{{ stat.value }}</span>
            </p>
          </article>
        </div>

        <h4 class="mb-3">Results by Quad</h4>
        <div class="quad-grid">
          <QuadCard
            v-for="quadCard in quadCards"
            :key="quadCard.label"
            :label="quadCard.label"
            :quad="quadCard.quad"
          />
        </div>
      </div>

      <div class="team-right">
        <section class="game-log-card">
          <h4>Game Log</h4>
          <p class="mb-4 sos-line">
            SOS: {{ sosOverallRank }} | Non-conference SOS:
            {{ sosNonConferenceRank }}
          </p>
          <div class="game-log-table-wrap">
            <table class="game-log-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Opponent</th>
                  <th>Result</th>
                  <th>Location</th>
                  <th>Record</th>
                  <th>Conf</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(game, index) in gameLog"
                  :key="`${game.date}-${game.opponent}-${index}`"
                  :class="
                    isResultWin(game.result) ? 'game-row-win' : 'game-row-loss'
                  "
                >
                  <td>{{ formatGameDate(game.date) }}</td>
                  <td
                    v-html="
                      formatOpponentWithRank(game.opponent, game.opponentRank)
                    "
                  ></td>
                  <td
                    :class="
                      isResultWin(game.result) ? 'result-win' : 'result-loss'
                    "
                  >
                    {{ formatScoreOnly(game.result) }}
                  </td>
                  <td>{{ game.location }}</td>
                  <td>{{ game.record }}</td>
                  <td>{{ game.conferenceRecord || "-" }}</td>
                </tr>
                <tr v-if="gameLog.length === 0">
                  <td colspan="6" class="text-muted text-center py-3">
                    No game log data available.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </section>
</template>

<style scoped>
.team-page {
  background: #fff;
}

.team-layout {
  display: grid;
  grid-template-columns: minmax(0, 60%) minmax(0, 40%);
  gap: 14px;
  align-items: stretch;
}

.team-left {
  min-width: 0;
}

.team-hero {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 12px;
}

.team-header {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

h2 {
  margin: 0;
}

.record-line, .sos-line {
  color: #4c454d;
  font-style: italic;
  font-weight: 500;
  font-size: 20px;
  margin: 0;
  align-self: flex-end;
}

.sos-line {
  font-size: 16px;
}

.extra-bold {
  font-weight: 900;
}

.team-logo {
  width: 72px;
  height: 72px;
  object-fit: contain;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.team-right {
  min-width: 0;
}

.game-log-card {
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  height: 100%;
  margin-top: 12px;
}

.game-log-table-wrap {
  max-height: 860px;
  overflow: auto;
  border: 0;
  border-radius: 6px;
}

.game-log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}

.game-log-table th,
.game-log-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #e9ecef;
  white-space: nowrap;
  text-align: left;
}

.game-log-table thead th {
  position: sticky;
  top: 0;
  background: #f5f6f8;
  z-index: 1;
  font-weight: 700;
}

.game-row-win {
  background: #e1f0e5;
}

.game-row-loss {
  background: #f7e2e2;
}

.result-win {
  color: #2c7a4b;
  font-weight: 700;
}

.result-loss {
  color: #b24f4f;
  font-weight: 700;
}

.stat-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 10px;
  background: #f8f9fa;
}

.label {
  margin: 0;
  font-size: 0.8rem;
  color: #6c757d;
}

.value {
  margin: 4px 0 0;
  font-size: 1rem;
  font-weight: 600;
}

.rank-chip {
  display: inline-block;
  min-width: 2.25rem;
  padding: 2px 8px;
  border-radius: 999px;
  text-align: center;
}

.value-detail {
  margin-left: 6px;
  color: #6c757d;
  font-size: 14px;
  font-style: italic;
  font-weight: 500;
}

.quad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.back-button {
  margin-bottom: 14px;
}

@media only screen and (max-width: 600px) {
  .team-layout {
    grid-template-columns: 1fr;
  }

  .team-logo {
    width: 56px;
    height: 56px;
  }

  .team-right {
    width: 100%;
  }

  .game-log-table {
    font-size: 0.8rem;
  }

  .game-log-table th,
  .game-log-table td {
    padding: 5px 6px;
  }

  .team-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0px;
  }

  .game-log-card {
    margin-top: 0px;
  }
}
</style>
