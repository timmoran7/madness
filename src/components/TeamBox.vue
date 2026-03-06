<script setup lang="ts">
interface TeamBoxProps {
  logo: string;
  teamName: string;
  logoFirst?: boolean;
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
      <p class="team-summary-hint text-muted mb-0">click for team breakdown</p>
    </button>
  </div>
</template>

<style scoped>
.team-info {
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-stack {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 90px;
}

.team-summary-hint {
  font-size: 0.85rem;
  max-width: 90px;
  text-align: center;
  position: absolute;
  top: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  width: max-content;
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
  .logo-stack {
    min-height: 40px;
  }

  .banner-pic {
    height: 40px;
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