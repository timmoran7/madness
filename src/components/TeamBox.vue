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
    </button>
  </div>
</template>

<style scoped>
.team-info {
  display: flex;
  align-items: center;
  justify-content: center;
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