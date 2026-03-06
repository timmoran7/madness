<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import MatchupTable from "@/components/MatchupTable.vue";
import UpsetTable from "@/components/UpsetTable.vue";
import TeamBox from "@/components/TeamBox.vue";
import pictureMappings from "@/data/picMappings.json";
import upsetData from "@/data/upsetData.json";
import matchupData from "@/data/matchupData.json";
import upsetTableData from "@/data/upsetTableData.json";
import type {
  MatchupTableDataType,
  CompactMatchupDataType,
  CompactUpsetTableDataType,
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

const picMappings: { [key: string]: string } = pictureMappings;
const upsetFactors: { [key: string]: { index: number; upset: number } } =
  upsetData;

const typedMatchupData = matchupData as CompactMatchupDataType;
const typedUpsetTableData = upsetTableData as CompactUpsetTableDataType;

const currentMatchupData = computed<MatchupTableDataType | null>(() => {
  if (!selectedRegion.value || !selectedMatchup.value) {
    return null;
  }

  const matchupTeams =
    typedMatchupData.regions[selectedRegion.value]?.[selectedMatchup.value];

  if (!matchupTeams) {
    return null;
  }

  return {
    columns: typedMatchupData.columns,
    teams: matchupTeams.map((team) => {
      const teamName = String(team[0] ?? "");
      const teamStats = Array.isArray(team[1]) ? team[1].map(String) : [];

      return {
        name: teamName,
        stats: teamStats.map((value) => ({ value })),
      };
    }),
  };
});

const currentUpsetData = computed<UpsetTableDataType | null>(() => {
  if (!selectedMatchup.value) {
    return null;
  }

  const values = typedUpsetTableData.matchups[selectedMatchup.value];
  if (!values) {
    return null;
  }

  return {
    columns: typedUpsetTableData.columns,
    values,
  };
});

const methodologyExplanation: string =
  "The <strong>Madness Index (MI)</strong> is a metric that \
measures the <strong>strength of common upset indicators</strong> present in a March Madness matchup. The MI is calculated based on research from KenPom and the New York Times \
boiling down to rebounding, turnovers, three point profile, and pacing. \
The MI is out of 10: an upset profile can be considered <strong>fair above 6, strong above 7, and extremely strong above 8</strong>. \
Upset chance is a less fun but more practical metric which spits out probabilities from a regression model trained on ten years' worth of data (regular + postseason). \
Enjoy!";

const matchupFiles: { [key: string]: string[] } = Object.keys(
  typedMatchupData.regions,
).reduce(
  (acc, region) => {
    acc[region] = Object.keys(typedMatchupData.regions[region]);
    return acc;
  },
  {} as { [key: string]: string[] },
);

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

  const team1 = selectedMatchup.value.split("_")[0];
  const team2 = selectedMatchup.value.split("_")[1];
  favLogo.value = `/madness/logos/${picMappings[team1]}`;
  dawgLogo.value = `/madness/logos/${picMappings[team2]}`;

  const matchupFactors = upsetFactors[selectedMatchup.value];
  if (!matchupFactors) {
    return;
  }

  miFactor.value = matchupFactors.index;
  upsetChance.value = matchupFactors.upset;

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
    params: { teamName },
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
</script>

<template>
  <div class="container mt-3">
    <div class="d-flex justify-content-center mb-3">
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
      :class="['d-flex ovr-banner mb-2', { 'ovr-banner-selected': selectedMatchup }]"
    >
      <TeamBox
        :logo="favLogo"
        :team-name="selectedMatchup ? selectedMatchup.split('_')[0] : ''"
        @logo-click="openTeamPage"
      />
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
      <TeamBox
        :logo="dawgLogo"
        :team-name="selectedMatchup ? selectedMatchup.split('_')[1] : ''"
        :logo-first="true"
        @logo-click="openTeamPage"
      />
    </div>
    <div v-if="dawgLogo" class="d-flex justify-content-center mb-4">
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
  gap: 15px;
  margin-bottom: -8px;
}

.ovr-banner-selected {
  margin-top: -20px;
}

.form-select {
  height: 50px;
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
  }
}
</style>
