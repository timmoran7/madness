<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";

interface TeamPageStats {
  offEfficiency: TeamStatDetail;
  defEfficiency: TeamStatDetail;
  height: TeamStatDetail;
  continuity: TeamStatDetail;
  experience: TeamStatDetail;
  benchMinutes: TeamStatDetail;
  sosOverall: TeamStatDetail;
  sosNonConference: TeamStatDetail;
  overallRank: string;
  record: string;
}

interface TeamStatDetail {
  rank: string;
  value: string;
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

defineProps<{
  teamName: string;
  teamLogo: string;
  gameLogImage: string;
  stats: TeamPageStats;
  quads: TeamQuadResults;
}>();

const router = useRouter();
const route = useRoute();

const goBack = () => {
  if (!route.query.region || !route.query.matchup) {
    router.push({ name: "matchup" });
    return;
  }

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
                ><sup>{{ getOrdinalSuffix(stats.overallRank) }}</sup> in KenPom
              </p>
            </div>
            <p class="mb-0 text-muted">Team overview and full quad results</p>
          </div>
        </div>

        <div class="stats-grid mb-4">
          <article class="stat-card">
            <p class="label">Off Efficiency Rank</p>
            <p class="value">
              <span>{{ stats.offEfficiency.rank }}</span>
              <span class="value-detail">{{ stats.offEfficiency.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">Def Efficiency Rank</p>
            <p class="value">
              <span>{{ stats.defEfficiency.rank }}</span>
              <span class="value-detail">{{ stats.defEfficiency.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">Height</p>
            <p class="value">
              <span>{{ stats.height.rank }}</span>
              <span class="value-detail">{{ stats.height.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">Continuity</p>
            <p class="value">
              <span>{{ stats.continuity.rank }}</span>
              <span class="value-detail">{{ stats.continuity.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">Experience</p>
            <p class="value">
              <span>{{ stats.experience.rank }}</span>
              <span class="value-detail">{{ stats.experience.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">Bench Minutes</p>
            <p class="value">
              <span>{{ stats.benchMinutes.rank }}</span>
              <span class="value-detail">{{ stats.benchMinutes.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">SOS Overall</p>
            <p class="value">
              <span>{{ stats.sosOverall.rank }}</span>
              <span class="value-detail">{{ stats.sosOverall.value }}</span>
            </p>
          </article>
          <article class="stat-card">
            <p class="label">SOS Non-Conf</p>
            <p class="value">
              <span>{{ stats.sosNonConference.rank }}</span>
              <span class="value-detail">{{
                stats.sosNonConference.value
              }}</span>
            </p>
          </article>
        </div>

        <h4 class="mb-3">Results by Quad</h4>
        <div class="quad-grid">
          <article class="quad-card">
            <div class="quad-head">
              <h5 class="mb-0">Q1</h5>
              <strong>{{ quads.q1.record }}</strong>
            </div>
            <ul>
              <li v-for="game in quads.q1.games" :key="`q1-${game}`" :class="isWin(game) ? 'game-win' : 'game-loss'">
                {{ game }}
              </li>
              <li v-if="quads.q1.games.length === 0" class="text-muted">
                No games listed
              </li>
            </ul>
          </article>

          <article class="quad-card">
            <div class="quad-head">
              <h5 class="mb-0">Q2</h5>
              <strong>{{ quads.q2.record }}</strong>
            </div>
            <ul>
              <li v-for="game in quads.q2.games" :key="`q2-${game}`" :class="isWin(game) ? 'game-win' : 'game-loss'">
                {{ game }}
              </li>
              <li v-if="quads.q2.games.length === 0" class="text-muted">
                No games listed
              </li>
            </ul>
          </article>

          <article class="quad-card">
            <div class="quad-head">
              <h5 class="mb-0">Q3</h5>
              <strong>{{ quads.q3.record }}</strong>
            </div>
            <ul>
              <li v-for="game in quads.q3.games" :key="`q3-${game}`" :class="isWin(game) ? 'game-win' : 'game-loss'">
                {{ game }}
              </li>
              <li v-if="quads.q3.games.length === 0" class="text-muted">
                No games listed
              </li>
            </ul>
          </article>

          <article class="quad-card">
            <div class="quad-head">
              <h5 class="mb-0">Q4</h5>
              <strong>{{ quads.q4.record }}</strong>
            </div>
            <ul>
              <li v-for="game in quads.q4.games" :key="`q4-${game}`" :class="isWin(game) ? 'game-win' : 'game-loss'">
                {{ game }}
              </li>
              <li v-if="quads.q4.games.length === 0" class="text-muted">
                No games listed
              </li>
            </ul>
          </article>
        </div>
      </div>

      <div class="team-right">
        <img :src="gameLogImage" alt="Game log" class="game-log-image" />
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
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 12px;
}

.team-header {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: baseline;
}

.record-line {
  color: #4c454d;
  font-style: italic;
  font-weight: 500;
  font-size: 20px;
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
  display: flex;
  justify-content: center;
  align-items: stretch;
}

.game-log-image {
  width: 100%;
  height: auto;
  max-height: 100%;
  object-fit: contain;
  border-radius: 6px;
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

.value-detail {
  margin-left: 6px;
  color: #6c757d;
  font-style: italic;
  font-weight: 500;
}

.quad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.quad-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 12px;
  background: #ffffff;
}

.quad-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.quad-card ul {
  margin: 0;
  padding-left: 16px;
  max-height: 240px;
  overflow: auto;
}

.quad-card li {
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.game-win {
  color: #2d7a4f;
}

.game-loss {
  color: #b85555;
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

  .game-log-image {
    display: block;
    width: 100%;
    height: auto;
    min-height: 0;
    max-height: none;
  }

  .quad-card ul {
    max-height: 180px;
  }
}
</style>
