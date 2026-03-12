<script setup lang="ts">
interface QuadBucket {
  record: string;
  games: string[];
}

defineProps<{
  label: string;
  quad: QuadBucket;
}>();

const isWin = (game: string): boolean => {
  const match = game.match(/^(\d+)-(\d+)/);
  if (!match) return false;
  return parseInt(match[1], 10) > parseInt(match[2], 10);
};
</script>

<template>
  <article class="quad-card">
    <div class="quad-head">
      <h5 class="mb-0">{{ label }}</h5>
      <strong>{{ quad.record }}</strong>
    </div>
    <ul>
      <li
        v-for="game in quad.games"
        :key="`${label}-${game}`"
        :class="isWin(game) ? 'game-win' : 'game-loss'"
      >
        {{ game }}
      </li>
      <li v-if="quad.games.length === 0" class="text-muted">No games listed</li>
    </ul>
  </article>
</template>

<style scoped>
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

@media only screen and (max-width: 600px) {
  .quad-card ul {
    max-height: 180px;
  }
}
</style>