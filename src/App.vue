<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import teams from "@/data/teams2026.json";

const router = useRouter();
const teamQuery = ref("");
const teamSearchInput = ref<HTMLInputElement | null>(null);
const isDropdownOpen = ref(false);

const teamNames = computed<string[]>(() => {
  return teams.sort((a, b) => a.localeCompare(b));
});

const filteredTeamNames = computed<string[]>(() => {
  const q = teamQuery.value.trim().toLowerCase();
  if (!q) return [];
  const startsWith = teamNames.value.filter((n) =>
    n.toLowerCase().startsWith(q),
  );
  const contains = teamNames.value.filter(
    (n) => !n.toLowerCase().startsWith(q) && n.toLowerCase().includes(q),
  );
  return [...startsWith, ...contains].slice(0, 12);
});

const resolveTeamName = (query: string): string | null => {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    return null;
  }

  const lowercaseQuery = trimmedQuery.toLowerCase();

  const exactMatch = teamNames.value.find(
    (name) => name.toLowerCase() === lowercaseQuery,
  );
  if (exactMatch) {
    return exactMatch;
  }

  const startsWithMatch = teamNames.value.find((name) =>
    name.toLowerCase().startsWith(lowercaseQuery),
  );
  if (startsWithMatch) {
    return startsWithMatch;
  }

  const containsMatch = teamNames.value.find((name) =>
    name.toLowerCase().includes(lowercaseQuery),
  );
  return containsMatch ?? null;
};

const onInputFocus = () => {
  isDropdownOpen.value = true;
};

const onInputBlur = () => {
  // Delay so a mousedown on a dropdown item fires before we close the list
  window.setTimeout(() => {
    isDropdownOpen.value = false;
  }, 150);
};

const selectTeam = (teamName: string) => {
  isDropdownOpen.value = false;
  teamQuery.value = teamName;
  teamSearchInput.value?.blur();
  router.push({ name: "team", params: { teamName } });
};

const goToTeamPage = async () => {
  isDropdownOpen.value = false;

  const resolvedTeamName = resolveTeamName(teamQuery.value);
  if (!resolvedTeamName) {
    return;
  }

  const wasPartialMatch =
    teamQuery.value.trim().toLowerCase() !== resolvedTeamName.toLowerCase();

  teamQuery.value = resolvedTeamName;

  if (wasPartialMatch) {
    isDropdownOpen.value = true;
    await nextTick();
    teamSearchInput.value?.focus();
    teamSearchInput.value?.setSelectionRange(0, resolvedTeamName.length);
    await new Promise((resolve) => window.setTimeout(resolve, 120));
    isDropdownOpen.value = false;
  }

  router.push({ name: "team", params: { teamName: resolvedTeamName } });
  teamSearchInput.value?.blur();
};

const goHome = () => {
  router.replace({ name: "matchup" });
};
</script>

<template>
  <div>
    <div class="container mt-5">
      <div class="position-relative text-center mb-4">
        <form class="team-search" @submit.prevent="goToTeamPage">
          <input
            ref="teamSearchInput"
            v-model="teamQuery"
            @focus="onInputFocus"
            @blur="onInputBlur"
            @input="isDropdownOpen = true"
            class="form-control"
            type="search"
            placeholder="Search team"
            aria-label="Search for a team"
            autocomplete="off"
          />
          <ul
            v-if="isDropdownOpen && filteredTeamNames.length > 0"
            class="team-dropdown"
          >
            <li
              v-for="teamName in filteredTeamNames"
              :key="teamName"
              @mousedown.prevent="selectTeam(teamName)"
              class="team-dropdown-item"
            >
              {{ teamName }}
            </li>
          </ul>
        </form>

        <img src="/public/bball.png" alt="Basketball" class="header-icon" />
        <h1 @click="goHome()" class="d-inline mx-3 site-hero">MADNESS.IO</h1>
        <img src="/public/bball.png" alt="Basketball" class="header-icon" />
      </div>
    </div>

    <RouterView />

    <div class="container">
      <footer class="text-center mt-5 text-muted">
        Credits: <a href="https://kenpom.com" target="_blank" rel="noopener noreferrer">KenPom.com</a>, <a href="https://bballnet.com" target="_blank" rel="noopener noreferrer">bballnet.com</a>
        <br>
        Contact: <a href="mailto:timthemoran@gmail.com">timthemoran@gmail.com</a>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.header-icon {
  height: 50px;
  width: 50px;
  margin-top: -22px;
}

.site-hero {
  cursor: pointer;
}

.team-search {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 240px;
  z-index: 100;
}

.team-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  margin: 2px 0 0;
  padding: 0;
  list-style: none;
  background: #fff;
  border: 1px solid #ced4da;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 260px;
  overflow-y: auto;
}

.team-dropdown-item {
  padding: 7px 12px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #212529;
}

.team-dropdown-item:hover {
  background-color: #e9ecef;
}

footer {
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .team-search {
    position: static;
    transform: none;
    margin: 0 auto 24px;
    width: 100%;
    max-width: 320px;
  }
}
</style>
