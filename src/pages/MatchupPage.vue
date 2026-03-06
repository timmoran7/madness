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
import rawTeamBoxData from "@/data/teamBoxData.json";
import type {
  TeamBoxStats,
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
const favTeamStats = ref<TeamBoxStats>({
  Quads: "",
  L10: "",
  Experience: "",
});
const dawgTeamStats = ref<TeamBoxStats>({
  Quads: "",
  L10: "",
  Experience: "",
});

const picMappings: { [key: string]: string } = pictureMappings;
const upsetFactors: { [key: string]: { index: number; upset: number } } =
  upsetData;

const teamBoxData = rawTeamBoxData as Record<string, TeamBoxStats>;

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

const syncMatchupQuery = () => {
  const query: Record<string, string> = {};

  if (selectedRegion.value) {
    query.region = selectedRegion.value;
  }

  if (selectedMatchup.value) {
    query.matchup = selectedMatchup.value;
  }

  router.replace({ path: "/", query });
};

const loadMatchups = () => {
  matchups.value = matchupFiles[selectedRegion.value] || [];
  showFactors.value = false;
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";
  syncMatchupQuery();
};

const loadMatchupContent = () => {
  if (!selectedMatchup.value) return;

  const team1 = selectedMatchup.value.split("_")[0];
  const team2 = selectedMatchup.value.split("_")[1];
  favLogo.value = `/madness/logos/${picMappings[team1]}`;
  dawgLogo.value = `/madness/logos/${picMappings[team2]}`;

  miFactor.value = upsetFactors[selectedMatchup.value].index;
  upsetChance.value = upsetFactors[selectedMatchup.value].upset;

  if (team1 in teamBoxData) {
    favTeamStats.value = teamBoxData[team1];
  }
  if (team2 in teamBoxData) {
    dawgTeamStats.value = teamBoxData[team2];
  }

  showFactors.value = true;
  showMethodology.value = false;
  syncMatchupQuery();
};

const openTeamPage = (teamName: string) => {
  if (!selectedMatchup.value || !teamName) {
    return;
  }

  router.push(`/${encodeURIComponent(teamName)}`);
};

const closeMatchupContent = () => {
  showMethodology.value = true;
  showFactors.value = false;
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";
  syncMatchupQuery();
};

onMounted(() => {
  const queryRegion =
    typeof route.query.region === "string" ? route.query.region : "";
  const queryMatchup =
    typeof route.query.matchup === "string" ? route.query.matchup : "";

  if (!queryRegion || !(queryRegion in matchupFiles)) {
    return;
  }

  selectedRegion.value = queryRegion;
  matchups.value = matchupFiles[queryRegion] || [];

  if (queryMatchup && matchups.value.includes(queryMatchup)) {
    selectedMatchup.value = queryMatchup;
    loadMatchupContent();
  }
});
</script>

<template>
  <div class="container mt-5">
    <div class="d-flex justify-content-center mb-4">
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
      class="d-flex justify-content-center ovr-banner"
    >
      <TeamBox
        :stats="favTeamStats"
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
        :stats="dawgTeamStats"
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
  margin-top: -20px;
  margin-bottom: -8px;
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
  }
}
</style>
