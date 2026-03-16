<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import MatchupTable from "@/components/MatchupTable.vue";
import UpsetTable from "@/components/UpsetTable.vue";
import TeamBox from "@/components/TeamBox.vue";
import teamLogoUrlsData from "@/data/teamLogoUrls.json";
import { normalizeTeamName } from "@/utils/teamName";
import upsetData from "@/data/upsetData.json";
import kpOvrStats from "@/data/kpOvrStats2026.json";
import seedProbabilities from "@/data/seedProbabilities.json";
import type {
  MatchupTableDataType,
  UpsetDataType,
  UpsetMatchupEntry,
  UpsetTableDataType,
} from "@/models";
import { channel } from "diagnostics_channel";

const router = useRouter();
const route = useRoute();

const CUSTOM_REGION_VALUE = "__any_two_teams__";
const regions = ["East", "West", "Midwest", "South"];
const selectedRegion = ref<string>("");
const matchups = ref<string[]>([]);
const showMethodology = ref<boolean>(true);
const countdownLabel = ref<string>("");
const customTeamOne = ref<string>("");
const customTeamTwo = ref<string>("");

const selectedMatchup = ref<string>("");
const favLogo = ref<string>("");
const dawgLogo = ref<string>("");
const miFactor = ref<number>(0);
const upsetChance = ref<number>(0);
const bracketReleaseAt = new Date("2026-03-15T17:30:00-05:00");
let countdownIntervalId: number | null = null;

const teamLogoUrls: Record<string, string> = teamLogoUrlsData;
const typedUpsetData = upsetData as UpsetDataType;

const NON_STAT_KEYS = new Set(["seed", "conference", "record"]);

const kpStats = kpOvrStats as unknown as Record<
  string,
  Record<string, [number, string]> & { seed: number; conference: string }
>;
const seedProbs = seedProbabilities as Record<string, number>;

const resolveUpsetMatchupKey = (matchupKey: string): string | null => {
  if (typedUpsetData.matchups[matchupKey]) {
    return matchupKey;
  }

  const [team1, team2] = matchupKey.split("_");
  if (!team1 || !team2) {
    return null;
  }

  const reversedMatchupKey = `${team2}_${team1}`;
  if (typedUpsetData.matchups[reversedMatchupKey]) {
    return reversedMatchupKey;
  }

  return null;
};

const allTeams = computed<string[]>(() => {
  const teamSet = new Set<string>();
  Object.keys(typedUpsetData.regions).forEach((regionKey: string) => {
    const region = typedUpsetData.regions[regionKey];
    region.forEach((matchup: string) => {
      const [team1, team2] = matchup.split("_");
      if (team1) teamSet.add(team1);
      if (team2) teamSet.add(team2);
    });
  });
  return Array.from(teamSet).sort();
});
const isCustomMode = computed<boolean>(
  () => selectedRegion.value === CUSTOM_REGION_VALUE,
);
const hasCustomPair = computed<boolean>(() =>
  Boolean(customTeamOne.value && customTeamTwo.value),
);
const hideRegionSelect = computed<boolean>(() => isCustomMode.value);
const hasUpsetEntry = computed<boolean>(() => {
  if (!selectedMatchup.value) return false;
  return Boolean(resolveUpsetMatchupKey(selectedMatchup.value));
});
const showFactors = computed<boolean>(() => {
  const leftSeed = teamInfo.value.fav?.seed;
  const rightSeed = teamInfo.value.dawg?.seed;
  const favoredSeed =
    leftSeed != null && rightSeed != null
      ? Math.min(leftSeed, rightSeed)
      : (leftSeed ?? rightSeed);
  const dawgSeed = favoredSeed === leftSeed ? rightSeed : leftSeed;
  const seedDiff =
    dawgSeed != null && favoredSeed != null ? dawgSeed - favoredSeed : null;
  return Boolean(
    selectedMatchup.value &&
      hasUpsetEntry.value &&
      seedDiff != null &&
      seedDiff >= 4, // only show factors for upsets of 4+ seeds, where the MI is more meaningful
  );
});

const showHomeRankings = computed<boolean>(
  () => !selectedRegion.value && !selectedMatchup.value && !isCustomMode.value,
);

const matchupRankings = computed(() =>
  Object.entries(typedUpsetData.matchups).map(
    ([matchup, entry]: [string, UpsetMatchupEntry]) => ({
      matchup,
      first: entry.firstRound,
      label: matchup.replace("_", " vs. "),
      upsetChance: entry.upset,
      madnessIndex: entry.index,
    }),
  ),
);

const filteredMatchupRankings = computed(() =>
  matchupRankings.value.filter((ranking) => {
    const [team1Raw, team2Raw] = ranking.matchup.split("_");
    const team1Seed = kpStats[normalizeTeamName(team1Raw)]?.seed;
    const team2Seed = kpStats[normalizeTeamName(team2Raw)]?.seed;

    if (team1Seed == null || team2Seed == null) {
      return true;
    }

    const lowerSeed = Math.min(team1Seed, team2Seed);
    const higherSeed = Math.max(team1Seed, team2Seed);
    return (
      !(
        (lowerSeed === 7 && higherSeed === 10) ||
        (lowerSeed === 8 && higherSeed === 9)
      ) && ranking.first === "yes"
    );
  }),
);

const topUpsetRankings = computed(() =>
  [...filteredMatchupRankings.value]
    .sort(
      (left, right) =>
        right.upsetChance - left.upsetChance ||
        right.madnessIndex - left.madnessIndex,
    )
    .slice(0, 5),
);

const topMadnessRankings = computed(() =>
  [...filteredMatchupRankings.value]
    .sort(
      (left, right) =>
        right.madnessIndex - left.madnessIndex ||
        right.upsetChance - left.upsetChance,
    )
    .slice(0, 5),
);

const teamInfo = computed(() => {
  if (!selectedMatchup.value) return { fav: null, dawg: null };
  const [t1Raw, t2Raw] = selectedMatchup.value.split("_");
  const t1 = kpStats[normalizeTeamName(t1Raw)];
  const t2 = kpStats[normalizeTeamName(t2Raw)];
  return {
    fav: t1
      ? {
          seed: t1.seed,
          record: t1["KenPom Ovr."]?.[1] ?? null,
          conference: t1.conference ?? null,
        }
      : null,
    dawg: t2
      ? {
          seed: t2.seed,
          record: t2["KenPom Ovr."]?.[1] ?? null,
          conference: t2.conference ?? null,
        }
      : null,
  };
});

const seedAvgLabel = computed<string | null>(() => {
  if (!selectedMatchup.value) return null;
  const [t1Raw, t2Raw] = selectedMatchup.value.split("_");
  const t1 = kpStats[normalizeTeamName(t1Raw)];
  const t2 = kpStats[normalizeTeamName(t2Raw)];
  if (!t1 || !t2) return null;
  const s1 = t1.seed;
  const s2 = t2.seed;
  if (!s1 || !s2) return null;
  const lowerSeed = Math.max(s1, s2); // higher number = lower seed (the underdog)
  const prob = seedProbs[String(lowerSeed)];
  if (prob == null) return null;
  const higherSeed = Math.min(s1, s2);
  return `${higherSeed}-${lowerSeed} avg: ${(prob * 100).toFixed(2)}%`;
});

const mobileTeamBoxOffsetPx = computed<number>(() => {
  const defaultLabelLength = "Select a Matchup".length;
  const longestMatchupLabelLength = matchups.value.reduce((maxLen, matchup) => {
    const labelLength = matchup.replace("_", " vs. ").length;
    return Math.max(maxLen, labelLength);
  }, defaultLabelLength);

  // Longer matchup labels produce wider selects, so taper the extra offset down.
  const offset = (1 / longestMatchupLabelLength) * 400;
  return offset;
});

const currentMatchupData = computed<MatchupTableDataType | null>(() => {
  if (!selectedMatchup.value) return null;

  const [team1Raw, team2Raw] = selectedMatchup.value.split("_");
  const team1Key = normalizeTeamName(team1Raw);
  const team2Key = normalizeTeamName(team2Raw);
  const team1Stats = kpStats[team1Key];
  const team2Stats = kpStats[team2Key];

  if (!team1Stats || !team2Stats) return null;

  const columns = Object.keys(team1Stats).filter((k) => !NON_STAT_KEYS.has(k));

  return {
    columns,
    teams: [
      {
        name: team1Raw,
        stats: columns.map((col) => ({
          value: String(team1Stats[col]?.[0] ?? ""),
        })),
      },
      {
        name: team2Raw,
        stats: columns.map((col) => ({
          value: String(team2Stats[col]?.[0] ?? ""),
        })),
      },
    ],
  };
});

const currentUpsetData = computed<UpsetTableDataType | null>(() => {
  if (!selectedMatchup.value) return null;

  const matchupKey = resolveUpsetMatchupKey(selectedMatchup.value);
  if (!matchupKey) return null;

  const entry = typedUpsetData.matchups[matchupKey];
  if (!entry) return null;

  return {
    columns: typedUpsetData.columns,
    values: entry.factors,
  };
});

const preTourneyMethodologyExplanation: string =
  "Welcome to March! <b>Search</b> for current tournament, auto-bid, and bubble teams to view their advanced stats, NET results, and game logs. \
Or, <b>explore last year's bracket</b> matchups with this year's stats. Come back when the bracket releases for updated matchups and statistics!";
const methodologyExplanation: string =
  "Welcome to March! Search for tournament teams to view their advanced stats, NET results, and game logs. \
<ul><li>The <strong>Madness Index (MI)</strong> is a metric that measures the <strong>strength of common upset indicators</strong> present, \
it's calculated based on research from KenPom and the New York Times. \
The MI is out of 10: an upset profile can be considered <strong>fair above 6, strong above 7, and extremely strong above 8</strong>.</li> \
<li>Upset chance is a less fun but more practical metric which spits out probabilities \
from a regression model trained on ten years' worth of data (regular + postseason). Enjoy!</li></ul>";

const matchupFiles: { [key: string]: string[] } = typedUpsetData.regions ?? {};
const matchupLocations: { [key: string]: string[] } =
  typedUpsetData.locations ?? {};

const currentLocation = computed<string | null>(() => {
  if (!selectedMatchup.value || isCustomMode.value) {
    return null;
  }

  const regionMatchups = matchupFiles[selectedRegion.value] ?? [];
  const matchupIndex = regionMatchups.indexOf(selectedMatchup.value);
  if (matchupIndex < 0) {
    return null;
  }

  const regionLocations = matchupLocations[selectedRegion.value] ?? [];
  return regionLocations[matchupIndex] ?? null;
});

const updateCountdownLabel = () => {
  const remainingMs = bracketReleaseAt.getTime() - Date.now();

  if (remainingMs <= 0) {
    countdownLabel.value = "Bracket release is live.";
    return;
  }

  const totalSeconds = Math.floor(remainingMs / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  countdownLabel.value = `${days}d ${String(hours).padStart(2, "0")}h ${String(
    minutes,
  ).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
};

const syncRouteQuery = (
  region: string,
  matchup: string,
  customTeam1 = "",
  customTeam2 = "",
) => {
  router.replace({
    name: "matchup",
    query: {
      region: region || undefined,
      matchup: matchup || undefined,
      team1: customTeam1 || undefined,
      team2: customTeam2 || undefined,
    },
  });
};

const resetMatchupSelection = () => {
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";
  miFactor.value = 0;
  upsetChance.value = 0;
  showMethodology.value = true;
};

const activateCustomMode = () => {
  selectedRegion.value = CUSTOM_REGION_VALUE;
  matchups.value = [];
  resetMatchupSelection();
  syncRouteQuery("", "", customTeamOne.value, customTeamTwo.value);
};

const clearCustomMode = () => {
  selectedRegion.value = "";
  customTeamOne.value = "";
  customTeamTwo.value = "";
  matchups.value = [];
  resetMatchupSelection();
  syncRouteQuery("", "");
};

const buildCustomMatchup = () => {
  if (!isCustomMode.value) return;

  if (!customTeamOne.value || !customTeamTwo.value) {
    resetMatchupSelection();
    syncRouteQuery("", "", customTeamOne.value, customTeamTwo.value);
    return;
  }

  if (customTeamOne.value === customTeamTwo.value) {
    resetMatchupSelection();
    syncRouteQuery("", "", customTeamOne.value, customTeamTwo.value);
    return;
  }

  selectedMatchup.value = `${customTeamOne.value}_${customTeamTwo.value}`;
  loadMatchupContent();
};

const loadMatchups = () => {
  if (selectedRegion.value === CUSTOM_REGION_VALUE) {
    activateCustomMode();
    return;
  }

  customTeamOne.value = "";
  customTeamTwo.value = "";
  matchups.value = matchupFiles[selectedRegion.value] || [];
  resetMatchupSelection();

  syncRouteQuery(selectedRegion.value, "");
};

const loadMatchupContent = () => {
  if (!selectedMatchup.value) return;

  const team1 = normalizeTeamName(selectedMatchup.value.split("_")[0]);
  const team2 = normalizeTeamName(selectedMatchup.value.split("_")[1]);
  favLogo.value = teamLogoUrls[team1] ?? "";
  dawgLogo.value = teamLogoUrls[team2] ?? "";

  const upsetMatchupKey = resolveUpsetMatchupKey(selectedMatchup.value);
  const matchupEntry = upsetMatchupKey
    ? typedUpsetData.matchups[upsetMatchupKey]
    : undefined;
  if (matchupEntry) {
    miFactor.value = matchupEntry.index;
    upsetChance.value = matchupEntry.upset;
  } else {
    miFactor.value = 0;
    upsetChance.value = 0;
  }
  showMethodology.value = false;

  syncRouteQuery(
    selectedRegion.value === CUSTOM_REGION_VALUE ? "" : selectedRegion.value,
    selectedMatchup.value,
    selectedRegion.value === CUSTOM_REGION_VALUE ? customTeamOne.value : "",
    selectedRegion.value === CUSTOM_REGION_VALUE ? customTeamTwo.value : "",
  );
};

const openTeamPage = (teamName: string) => {
  if (!selectedMatchup.value || !teamName) {
    return;
  }

  const teamRoute = router.resolve({
    name: "team",
    params: { teamName: normalizeTeamName(teamName) },
    query: {
      region:
        typeof route.query.region === "string" ? route.query.region : undefined,
      matchup:
        typeof route.query.matchup === "string"
          ? route.query.matchup
          : undefined,
    },
  });

  window.open(teamRoute.href, "_blank", "noopener,noreferrer");
};

const closeMatchupContent = () => {
  resetMatchupSelection();

  syncRouteQuery(
    selectedRegion.value === CUSTOM_REGION_VALUE ? "" : selectedRegion.value,
    "",
    selectedRegion.value === CUSTOM_REGION_VALUE ? customTeamOne.value : "",
    selectedRegion.value === CUSTOM_REGION_VALUE ? customTeamTwo.value : "",
  );
};

const resetState = () => {
  selectedRegion.value = "";
  customTeamOne.value = "";
  customTeamTwo.value = "";
  matchups.value = [];
  resetMatchupSelection();
};

const applyRouteStateFromQuery = () => {
  const regionQuery =
    typeof route.query.region === "string" ? route.query.region : "";
  const matchupQuery =
    typeof route.query.matchup === "string" ? route.query.matchup : "";
  const teamOneQuery =
    typeof route.query.team1 === "string" ? route.query.team1 : "";
  const teamTwoQuery =
    typeof route.query.team2 === "string" ? route.query.team2 : "";

  if (!regionQuery && !matchupQuery && !teamOneQuery && !teamTwoQuery) {
    resetState();
    return;
  }

  const hasTeamOne = Boolean(
    teamOneQuery && kpStats[normalizeTeamName(teamOneQuery)],
  );
  const hasTeamTwo = Boolean(
    teamTwoQuery && kpStats[normalizeTeamName(teamTwoQuery)],
  );

  if (!regionQuery && (teamOneQuery || teamTwoQuery)) {
    selectedRegion.value = CUSTOM_REGION_VALUE;
    matchups.value = [];
    customTeamOne.value = hasTeamOne ? teamOneQuery : "";
    customTeamTwo.value = hasTeamTwo ? teamTwoQuery : "";

    if (
      matchupQuery &&
      hasTeamOne &&
      hasTeamTwo &&
      matchupQuery === `${customTeamOne.value}_${customTeamTwo.value}`
    ) {
      selectedMatchup.value = matchupQuery;
      loadMatchupContent();
      return;
    }

    buildCustomMatchup();
    return;
  }

  if (!regionQuery && matchupQuery) {
    const [team1, team2] = matchupQuery.split("_");
    if (
      team1 &&
      team2 &&
      kpStats[normalizeTeamName(team1)] &&
      kpStats[normalizeTeamName(team2)]
    ) {
      selectedRegion.value = CUSTOM_REGION_VALUE;
      matchups.value = [];
      customTeamOne.value = team1;
      customTeamTwo.value = team2;
      selectedMatchup.value = matchupQuery;
      loadMatchupContent();
      return;
    }
  }

  if (!regionQuery || !matchupFiles[regionQuery]) {
    resetState();
    return;
  }

  selectedRegion.value = regionQuery;
  customTeamOne.value = "";
  customTeamTwo.value = "";
  matchups.value = matchupFiles[regionQuery] || [];

  if (!matchupQuery || !matchups.value.includes(matchupQuery)) {
    resetMatchupSelection();
    return;
  }

  selectedMatchup.value = matchupQuery;
  loadMatchupContent();
};

const boostUpsetChance = (chance: number): number => {
  return (chance * 100) < 20 ? chance * 100 * 1.3 : chance * 100;
};

onMounted(() => {
  updateCountdownLabel();
  countdownIntervalId = window.setInterval(updateCountdownLabel, 1000);
  applyRouteStateFromQuery();
});

onUnmounted(() => {
  if (countdownIntervalId !== null) {
    clearInterval(countdownIntervalId);
  }
});

watch(
  () => route.query,
  () => {
    applyRouteStateFromQuery();
  },
);

watch([customTeamOne, customTeamTwo], () => {
  buildCustomMatchup();
});
</script>

<template>
  <div class="container main-ctr">
    <div v-if="!hideRegionSelect" class="d-flex justify-content-center">
      <select
        v-model="selectedRegion"
        @change="loadMatchups"
        class="form-select w-auto"
      >
        <option value="" disabled>Select a Region</option>
        <option v-for="region in regions" :key="region" :value="region">
          {{ region }}
        </option>
      </select>
    </div>

    <div v-if="!isCustomMode" class="d-flex justify-content-center">
      <button class="btn btn-link any-two-trigger" @click="activateCustomMode">
        Or pick any two teams
      </button>
    </div>

    <p class="text-center exclude-note" v-if="showHomeRankings">
      <em>Excludes 7/10 + 8/9 games</em>
    </p>
    <div v-if="showHomeRankings" class="home-rankings">
      <section class="home-ranking-card">
        <h3 class="home-ranking-title">Top Upset Chances</h3>
        <ul class="home-ranking-list">
          <li
            v-for="ranking in topUpsetRankings"
            :key="`upset-${ranking.matchup}`"
            class="home-ranking-item"
          >
            <span class="home-ranking-matchup">{{ ranking.label }}</span>
            <strong>{{ boostUpsetChance(ranking.upsetChance).toFixed(2) }}%</strong>
          </li>
        </ul>
      </section>

      <section class="home-ranking-card">
        <h3 class="home-ranking-title">Top Madness Indexes</h3>
        <ul class="home-ranking-list">
          <li
            v-for="ranking in topMadnessRankings"
            :key="`madness-${ranking.matchup}`"
            class="home-ranking-item"
          >
            <span class="home-ranking-matchup">{{ ranking.label }}</span>
            <strong>{{ ranking.madnessIndex.toFixed(2) }}</strong>
          </li>
        </ul>
      </section>
    </div>

    <div v-if="isCustomMode" class="any-two-container">
      <p class="any-two-title">Any Two Teams</p>
      <div class="any-two-anchor">
        <div class="team-box-abs team-box-left any-two-team-box">
          <TeamBox
            :logo="favLogo"
            :team-name="customTeamOne"
            :seed="teamInfo.fav?.seed ?? null"
            :record="teamInfo.fav?.record ?? null"
            :conference="teamInfo.fav?.conference ?? null"
            @logo-click="openTeamPage"
          />
        </div>
        <div class="any-two-selects">
          <select v-model="customTeamOne" class="form-select">
            <option value="" disabled>Select Team 1</option>
            <option
              v-for="team in allTeams"
              :key="`team1-${team}`"
              :value="team"
            >
              {{ team }}
            </option>
          </select>
          <span class="any-two-vs">vs.</span>
          <select v-model="customTeamTwo" class="form-select">
            <option value="" disabled>Select Team 2</option>
            <option
              v-for="team in allTeams"
              :key="`team2-${team}`"
              :value="team"
            >
              {{ team }}
            </option>
          </select>
        </div>
        <div class="team-box-abs team-box-right any-two-team-box">
          <TeamBox
            :logo="dawgLogo"
            :team-name="customTeamTwo"
            :logo-first="true"
            :seed="teamInfo.dawg?.seed ?? null"
            :record="teamInfo.dawg?.record ?? null"
            :conference="teamInfo.dawg?.conference ?? null"
            @logo-click="openTeamPage"
          />
        </div>
      </div>
      <div v-if="customTeamOne || customTeamTwo" class="any-two-mobile-preview">
        <TeamBox
          :logo="favLogo"
          :team-name="customTeamOne"
          :seed="teamInfo.fav?.seed ?? null"
          :record="teamInfo.fav?.record ?? null"
          :conference="teamInfo.fav?.conference ?? null"
          @logo-click="openTeamPage"
        />
        <button
          class="btn btn-sm btn-outline-secondary any-two-mobile-switch"
          @click="clearCustomMode"
        >
          Use region matchups
        </button>
        <TeamBox
          :logo="dawgLogo"
          :team-name="customTeamTwo"
          :logo-first="true"
          :seed="teamInfo.dawg?.seed ?? null"
          :record="teamInfo.dawg?.record ?? null"
          :conference="teamInfo.dawg?.conference ?? null"
          @logo-click="openTeamPage"
        />
      </div>
      <p
        v-if="customTeamOne && customTeamOne === customTeamTwo"
        class="same-team-hint"
      >
        Pick two different teams.
      </p>
      <div class="d-flex justify-content-center">
        <button
          class="btn btn-sm btn-outline-secondary any-two-desktop-switch"
          @click="clearCustomMode"
        >
          Use region matchups
        </button>
      </div>
    </div>

    <div
      v-if="matchups.length > 0 && !isCustomMode"
      :class="['ovr-banner', { 'ovr-banner-selected': selectedMatchup }]"
    >
      <div
        class="select-anchor"
        :style="{ '--mobile-team-box-offset': `${mobileTeamBoxOffsetPx}px` }"
      >
        <div class="team-box-abs team-box-left">
          <TeamBox
            :logo="favLogo"
            :team-name="selectedMatchup ? selectedMatchup.split('_')[0] : ''"
            :seed="teamInfo.fav?.seed ?? null"
            :record="teamInfo.fav?.record ?? null"
            :conference="teamInfo.fav?.conference ?? null"
            @logo-click="openTeamPage"
          />
        </div>
        <select
          v-model="selectedMatchup"
          @change="loadMatchupContent"
          class="form-select w-auto"
        >
          <option value="" disabled>Select a Matchup</option>
          <option v-for="matchup in matchups" :key="matchup" :value="matchup">
            {{ matchup.replace("_", " vs. ") }}
          </option>
        </select>
        <div class="team-box-abs team-box-right">
          <TeamBox
            :logo="dawgLogo"
            :team-name="selectedMatchup ? selectedMatchup.split('_')[1] : ''"
            :logo-first="true"
            :seed="teamInfo.dawg?.seed ?? null"
            :record="teamInfo.dawg?.record ?? null"
            :conference="teamInfo.dawg?.conference ?? null"
            @logo-click="openTeamPage"
          />
        </div>
      </div>
    </div>
    <div
      v-if="dawgLogo && !isCustomMode"
      class="d-flex justify-content-center mb-4 match-subheader"
    >
      <p class="click-hint"><em>click on logos for team breakdown</em></p>
      <p v-if="currentLocation">
        <strong>{{ currentLocation }}</strong>
      </p>
    </div>

    <div
      v-if="showFactors"
      :class="[
        'd-flex justify-content-center mb-4 upset-factors',
        { 'any-two-upset-factors': isCustomMode },
      ]"
    >
      <h5 class="mi text-center">
        <strong>MADNESS INDEX: {{ miFactor }} / 10</strong>
      </h5>
      <h5 class="factor text-center">
        <strong
          >Upset Chance:
          {{
            boostUpsetChance(upsetChance).toFixed(2)
          }}%</strong
        >
        <span v-if="seedAvgLabel && !hasCustomPair" class="seed-avg-hint">
          ({{ seedAvgLabel }})</span
        >
      </h5>
    </div>

    <div
      v-if="showMethodology"
      class="mt-4 p-3 border border-secondary rounded bg-light"
    >
      <p v-html="methodologyExplanation"></p>
    </div>
    <!-- <div v-if="showMethodology" class="countdown-wrapper">
      <p>
        Bracket releases:<br /><span class="countdown-label">{{
          countdownLabel
        }}</span>
      </p>
    </div> -->

    <div
      v-if="currentMatchupData"
      class="mt-4 p-3 border border-secondary rounded bg-light position-relative"
    >
      <button @click="closeMatchupContent" class="btn-close"></button>
      <p v-if="selectedMatchup && !hasUpsetEntry" class="missing-upset-text">
        No upset profile exists yet for this hypothetical matchup.
      </p>
      <UpsetTable
        class="upset-table"
        v-if="currentUpsetData && showFactors"
        :data="currentUpsetData"
      />
      <MatchupTable class="matchup-table" :data="currentMatchupData" />
    </div>
  </div>
</template>

<style scoped>
.container {
  margin-top: 30px;
}

.ovr-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.select-anchor {
  position: relative;
  display: inline-block;
}

.team-box-abs {
  position: absolute;
  top: 50%;
  transform: translateY(
    -45px
  ); /* aligns logo center (half of 90px) with select center */
}

.team-box-left {
  right: calc(100% + 20px);
}

.team-box-right {
  left: calc(100% + 20px);
}

.form-select {
  height: 50px;
  margin: 12px 0;
}

.match-subheader {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.match-subheader p {
  margin: 0;
}

.click-hint {
  font-size: 14px;
  color: #6c757d;
}

.seed-avg-hint {
  font-size: 0.8em;
  color: #6c757d;
  font-weight: normal;
}

.upset-factors {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.any-two-upset-factors {
  margin-top: 12px;
}

.mi {
  color: crimson;
}

.position-relative {
  position: relative;
}

.btn-close {
  position: absolute;
  top: 0;
  right: 0;
  margin: 10px;
}

.countdown-wrapper {
  display: flex;
  justify-content: center;
  text-align: center;
  margin-top: 12px;
}

.countdown-label {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  font-style: italic;
}

.any-two-trigger {
  margin-top: -12px;
  margin-bottom: 4px;
  font-size: 14px;
}

.home-rankings {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin: 18px auto 8px;
  max-width: 880px;
}

.home-ranking-card {
  padding: 16px 18px;
  border: 1px solid #ced4da;
  border-radius: 10px;
  background: #f8f9fa;
}

.home-ranking-title {
  margin: 0 0 12px;
  font-size: 1.05rem;
  text-align: center;
}

.home-ranking-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.home-ranking-item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 7px 0;
  border-top: 1px solid rgba(108, 117, 125, 0.18);
}

.home-ranking-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.home-ranking-matchup {
  color: #212529;
}

.any-two-container {
  margin-top: 8px;
  margin-bottom: 6px;
  text-align: center;
}

.any-two-title {
  margin: 0 0 10px;
  text-align: center;
  font-weight: 600;
}

.any-two-anchor {
  position: relative;
  display: inline-block;
}

.any-two-selects {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.any-two-team-box {
  display: none;
}

.any-two-mobile-preview {
  display: none;
}

.any-two-selects .form-select {
  width: min(300px, 42vw);
}

.any-two-vs {
  font-weight: 600;
  color: #6c757d;
}

.same-team-hint {
  margin: 2px 0 10px;
  text-align: center;
  color: #b02a37;
  font-size: 0.9rem;
}

.missing-upset-text {
  margin: 0 30px 10px 0;
  color: #6c757d;
  font-size: 0.95rem;
}

.main-ctr {
  margin-top: -8px;
}

.matchup-table,
.upset-table {
  margin-top: 8px;
}

@media only screen and (min-width: 1201px) {
  .any-two-team-box {
    display: block;
  }
}

@media only screen and (max-width: 600px) {
  .home-rankings {
    grid-template-columns: 1fr;
    gap: 12px;
    margin-top: 14px;
  }

  .ovr-banner {
    margin-bottom: 8px;
  }

  .mi,
  .factor {
    font-size: 18px;
  }

  .form-select {
    font-size: 14px;
  }

  .team-box-left {
    right: calc(100% + var(--mobile-team-box-offset));
  }

  .team-box-right {
    left: calc(100% + var(--mobile-team-box-offset));
  }

  .click-hint {
    font-size: 12px;
  }

  .countdown-label {
    font-size: 0.95rem;
    text-align: center;
  }

  .any-two-selects {
    flex-direction: column;
    gap: 0px;
  }

  .any-two-vs {
    display: none;
  }

  .any-two-selects .form-select {
    width: min(320px, 90vw);
  }

  .any-two-mobile-preview {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    margin: 8px 0 2px;
  }

  .any-two-mobile-switch {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-wrap: nowrap;
    min-height: 0;
    padding: 5px 9px;
    line-height: 1.22;
  }

  .any-two-mobile-preview :deep(.logo-stack) {
    min-height: 60px;
  }

  .any-two-mobile-preview :deep(.banner-pic) {
    height: 60px;
  }

  .any-two-desktop-switch {
    display: none;
  }

  .main-ctr {
    margin-top: -12px;
  }

  .exclude-note {
    margin-bottom: -4px;
  }
}
</style>
