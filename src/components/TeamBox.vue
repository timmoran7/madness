<script setup lang="ts">
import { computed } from "vue";
import type { TeamBoxStats } from "../models";

interface TeamBoxProps {
  logo: string;
  stats: TeamBoxStats;
  teamName: string;
  logoFirst?: boolean;
}

const props = withDefaults(defineProps<TeamBoxProps>(), {
  logoFirst: false,
});

const emit = defineEmits<{
  logoClick: [teamName: string];
}>();

const statsAlign = computed(() => {
  return props.logoFirst ? "left" : "right";
});
</script>

<template>
  <div class="team-info">
    <template v-if="props.logoFirst">
      <button
        type="button"
        class="logo-button"
        @click="emit('logoClick', props.teamName)"
        :disabled="!props.logo"
      >
        <img class="banner-pic" :src="props.logo" :alt="props.teamName" />
      </button>
      <ul class="list-unstyled mb-0" v-if="props.logo" :style="{ textAlign: statsAlign }">
        <li><strong>Quad 1: {{ props.stats.Quads }}</strong></li>
        <li><strong>L10: {{ props.stats.L10 }}</strong></li>
        <li><strong>Experience: {{ props.stats.Experience }}</strong></li>
      </ul>
    </template>
    <template v-else>
      <ul class="list-unstyled mb-0" v-if="props.logo" :style="{ textAlign: statsAlign }">
        <li><strong>Quad 1: {{ props.stats.Quads }}</strong></li>
        <li><strong>L10: {{ props.stats.L10 }}</strong></li>
        <li><strong>Experience: {{ props.stats.Experience }}</strong></li>
      </ul>
      <button
        type="button"
        class="logo-button"
        @click="emit('logoClick', props.teamName)"
        :disabled="!props.logo"
      >
        <img class="banner-pic" :src="props.logo" :alt="props.teamName" />
      </button>
    </template>
  </div>
</template>

<style scoped>
.team-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.banner-pic {
  height: 90px;
}

.logo-button {
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.logo-button:disabled {
  cursor: default;
}

@media only screen and (max-width: 600px) {
  .banner-pic {
    height: 40px;
  }
}

@media only screen and (max-width: 100px) {
  .banner-pic {
    height: 75px;
  }
}
</style>