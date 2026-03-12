<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
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
  UpsetTableDataType,
} from "@/models";

const router = useRouter();
const route = useRoute();

const regions = ["South", "East", "Midwest", "West"];
const selectedRegion = ref<string>("");
const matchups = ref<string[]>([]);
const showFactors = ref<boolean>(false);
const showMethodology = ref<boolean>(true);

const selectedMatchup = ref<string>("");
const favLogo = ref<string>("");
const dawgLogo = ref<string>("");
const miFactor = ref<number>(0);
const upsetChance = ref<number>(0);

const teamLogoUrls: Record<string, string> = teamLogoUrlsData;
const typedUpsetData = upsetData as UpsetDataType;

const NON_STAT_KEYS = new Set(["seed", "conference", "record"]);

const kpStats = kpOvrStats as unknown as Record<string, Record<string, [number, string]> & { seed: number; conference: string }>;
const seedProbs = seedProbabilities as Record<string, number>;

const teamInfo = computed(() => {
  if (!selectedMatchup.value) return { fav: null, dawg: null };
  const [t1Raw, t2Raw] = selectedMatchup.value.split("_");
  const t1 = kpStats[normalizeTeamName(t1Raw)];
  const t2 = kpStats[normalizeTeamName(t2Raw)];
  return {
    fav: t1 ? { seed: t1.seed, record: t1["KenPom Ovr."]?.[1] ?? null, conference: t1.conference ?? null } : null,
    dawg: t2 ? { seed: t2.seed, record: t2["KenPom Ovr."]?.[1] ?? null, conference: t2.conference ?? null } : null,
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

  const entry = typedUpsetData.matchups[selectedMatchup.value];
  if (!entry) return null;

  return {
    columns: typedUpsetData.columns,
    values: entry.factors,
  };
});

const methodologyExplanation: string =
  "The <strong>Madness Index (MI)</strong> is a metric that \
measures the <strong>strength of common upset indicators</strong> present in a March Madness matchup. The MI is calculated based on research from KenPom and the New York Times \
boiling down to rebounding, turnovers, three point profile, and pacing. \
The MI is out of 10: an upset profile can be considered <strong>fair above 6, strong above 7, and extremely strong above 8</strong>. \
Upset chance is a less fun but more practical metric which spits out probabilities from a regression model trained on ten years' worth of data (regular + postseason). \
Enjoy!";

const matchupFiles: { [key: string]: string[] } = typedUpsetData.regions ?? {};

const syncRouteQuery = (region: string, matchup: string) => {
  router.replace({
    name: "matchup",
    query: {
      region: region || undefined,
      matchup: matchup || undefined,
    },
  });
};

const loadMatchups = () => {
  matchups.value = matchupFiles[selectedRegion.value] || [];
  showFactors.value = false;
  showMethodology.value = true;
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";

  syncRouteQuery(selectedRegion.value, "");
};

const loadMatchupContent = () => {
  if (!selectedMatchup.value) return;

  const team1 = normalizeTeamName(selectedMatchup.value.split("_")[0]);
  const team2 = normalizeTeamName(selectedMatchup.value.split("_")[1]);
  favLogo.value = teamLogoUrls[team1] ?? "";
  dawgLogo.value = teamLogoUrls[team2] ?? "";

  const matchupEntry = typedUpsetData.matchups[selectedMatchup.value];
  if (!matchupEntry) {
    return;
  }

  miFactor.value = matchupEntry.index;
  upsetChance.value = matchupEntry.upset;

  showFactors.value = true;
  showMethodology.value = false;

  syncRouteQuery(selectedRegion.value, selectedMatchup.value);
};

const openTeamPage = (teamName: string) => {
  if (!selectedMatchup.value || !teamName) {
    return;
  }

  router.push({
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
};

const closeMatchupContent = () => {
  showMethodology.value = true;
  showFactors.value = false;
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";

  syncRouteQuery(selectedRegion.value, "");
};

const resetState = () => {
  selectedRegion.value = "";
  matchups.value = [];
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";
  showFactors.value = false;
  showMethodology.value = true;
};

onMounted(() => {
  const regionQuery =
    typeof route.query.region === "string" ? route.query.region : "";
  const matchupQuery =
    typeof route.query.matchup === "string" ? route.query.matchup : "";

  if (!regionQuery || !matchupFiles[regionQuery]) {
    return;
  }

  selectedRegion.value = regionQuery;
  matchups.value = matchupFiles[regionQuery] || [];

  if (!matchupQuery || !matchups.value.includes(matchupQuery)) {
    syncRouteQuery(selectedRegion.value, "");
    return;
  }

  selectedMatchup.value = matchupQuery;
  loadMatchupContent();
});

watch(
  () => route.query,
  (query) => {
    if (!query.region && !query.matchup) {
      resetState();
    }
  },
);
</script>

<template>
  <div class="container mt-3">
    <div class="d-flex justify-content-center">
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

    <div
      v-if="matchups.length > 0"
      :class="['ovr-banner', { 'ovr-banner-selected': selectedMatchup }]"
    >
      <div class="select-anchor">
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
    <div v-if="dawgLogo" class="d-flex justify-content-center mb-4 match-subheader">
      <p class="click-hint"><em>click on logos for team breakdown</em></p>
      <p><strong>Shmindianapolis, IN</strong></p>
    </div>

    <div
      v-if="showFactors"
      class="d-flex justify-content-center mb-4 upset-factors"
    >
      <h5 class="mi text-center">
        <strong>MADNESS INDEX: {{ miFactor }} / 10</strong>
      </h5>
      <h5 class="factor text-center">
        <strong>Upset Chance: {{ (upsetChance * 100).toFixed(2) }}%</strong>
        <span v-if="seedAvgLabel" class="seed-avg-hint"> ({{ seedAvgLabel }})</span>
      </h5>
    </div>

    <div
      v-if="showMethodology"
      class="mt-4 p-3 border border-secondary rounded bg-light"
    >
      <p v-html="methodologyExplanation"></p>
    </div>

    <div
      v-if="currentMatchupData"
      class="mt-4 p-3 border border-secondary rounded bg-light position-relative"
    >
      <button @click="closeMatchupContent" class="btn-close"></button>
      <UpsetTable v-if="currentUpsetData" :data="currentUpsetData" />
      <MatchupTable :data="currentMatchupData" />
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
  transform: translateY(-45px); /* aligns logo center (half of 90px) with select center */
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

@media only screen and (max-width: 600px) {
  .ovr-banner {
    gap: 9px;
    margin-top: 12px;
    margin-bottom: 8px;
  }
}
</style>
