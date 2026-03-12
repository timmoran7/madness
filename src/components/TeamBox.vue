<script setup lang="ts">
interface TeamBoxProps {
  logo: string;
  teamName: string;
  logoFirst?: boolean;
  seed?: number | null;
  record?: string | null;
  conference?: string | null;
}

const props = withDefaults(defineProps<TeamBoxProps>(), {
  logoFirst: false,
});

const emit = defineEmits<{
  logoClick: [teamName: string];
}>();
</script>

<template>
  <div class="team-info">
    <button
      v-if="props.logo"
      type="button"
      class="logo-stack logo-button"
      @click="emit('logoClick', props.teamName)"
      :disabled="!props.logo"
    >
        <img class="banner-pic" :src="props.logo" :alt="props.teamName" />
    </button>
    <div v-if="props.seed != null || props.record || props.conference" class="team-meta">
      <span class="seed" v-if="props.seed != null">({{ props.seed }})</span>
      <span class="record" v-if="props.record"><b>· </b>{{ props.record }}</span>
      <span class="conference" v-if="props.conference"><b>· </b>{{ props.conference }}</span>
    </div>
  </div>
</template>

<style scoped>
.team-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.team-meta {
  display: flex;
  flex-wrap: nowrap;
  white-space: nowrap;
  gap: 4px;
  font-size: 16px;
  margin-top: 3px;
  justify-content: center;
}

.seed {
  font-weight: 700;
}

.banner-pic {
  height: 90px;
}

.logo-button {
  position: relative;
  border: 0;
  border-radius: 4px;
  background: transparent;
  padding: 0;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.logo-button:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.logo-button:disabled {
  cursor: default;
}

@media only screen and (max-width: 600px) {
  .logo-stack {
    min-height: 40px;
  }

  .banner-pic {
    height: 40px;
  }

  .team-meta {
    flex-direction: column;
    align-items: center;
    gap: 0;
    font-size: 14px;
  }

  .team-meta b {
    display: none;
  }
}

@media only screen and (max-width: 100px) {
  .logo-stack {
    min-height: 75px;
  }

  .banner-pic {
    height: 75px;
  }
}
</style>