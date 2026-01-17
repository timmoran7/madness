<script setup lang="ts">
import { ref, computed } from "vue";
import MatchupTable from '@/components/MatchupTable.vue';
import UpsetTable from '@/components/UpsetTable.vue';
import pictureMappings from '@/data/picMappings.json'
import upsetData from '@/data/upsetData.json'
import matchupData from '@/data/matchupData.json'
import upsetTableData from '@/data/upsetTableData.json'

const regions = ["South", "East", "Midwest", "West"];
const selectedRegion = ref<string>("");
const matchups = ref<string[]>([]);
const selectedMatchup = ref<string>("");
const favLogo = ref<string>("");
const dawgLogo = ref<string>("");

const showFactors = ref<boolean>(false);
const miFactor = ref<number>(0);
const upsetChance = ref<number>(0);
const showMethodology = ref<boolean>(true);

const picMappings: { [key: string]: string } = pictureMappings;
const upsetFactors: { [key: string]: { index: number, upset: number } } = upsetData;

interface MatchupDataType {
  [key: string]: {
    columns: string[];
    teams: {
      name: string;
      stats: { value: string; color: string }[];
    }[];
  };
}

interface UpsetTableDataType {
  [key: string]: {
    columns: string[];
    values: { value: string; color: string }[];
  };
}

const typedMatchupData = matchupData as MatchupDataType;
const typedUpsetTableData = upsetTableData as UpsetTableDataType;

const currentMatchupData = computed(() => {
  return selectedMatchup.value && typedMatchupData[selectedMatchup.value] 
    ? typedMatchupData[selectedMatchup.value] 
    : null;
});

const currentUpsetData = computed(() => {
  return selectedMatchup.value && typedUpsetTableData[selectedMatchup.value] 
    ? typedUpsetTableData[selectedMatchup.value] 
    : null;
});

const methodologyExplanation: string = "The <strong>Madness Index (MI)</strong> is a metric that \
measures the <strong>strength of common upset indicators</strong> present in a March Madness matchup. The MI is calculated based on research from KenPom and the New York Times \
boiling down to rebounding, turnovers, three point profile, and pacing. Use it with a grain of salt as it has <strong>not (yet) been perfected by testing on previous years' outcomes</strong>. \
The MI is out of 10, but realistically an underdog will never approach this strength. The MI upset profile can be considered <strong>fair above 6, strong above 6.5, and extremely strong above 7</strong>. \
The upset chance is a rough formula based on the MI and the seeding of each team. It too has not (yet) been tested, consider it inspiration (and a reality check on the MI). \
Come back next year for a refined and tested version of Madness.IO!";

// Replace this with actual matchup filenames
const matchupFiles: { [key: string]: string[] } = {
  South: ["Auburn_Alabama St.", "Louisville_Creighton", "Michigan_UC San Diego", "Texas A&M_Yale", 
    "Mississippi_North Carolina", "Iowa St._Lipscomb", "Marquette_New Mexico", "Michigan St._Bryant"],
  East: ["Duke_American", "Duke_Mount St. Mary's", "Mississippi St._Baylor", "Oregon_Liberty", "Arizona_Akron", "BYU_VCU", 
    "Wisconsin_Montana", "Saint Mary's_Vanderbilt", "Alabama_Robert Morris"],
  Midwest: ["Houston_SIUE", "Gonzaga_Georgia", "Clemson_McNeese", "Purdue_High Point", "Illinois_Texas", "Illinois_Xavier", 
    "Kentucky_Troy", "UCLA_Utah St.", "Tennessee_Wofford"],
  West: ["Florida_Norfolk St.", "Connecticut_Oklahoma", "Memphis_Colorado St.", "Maryland_Grand Canyon", "Missouri_Drake",
    "Texas Tech_UNC Wilmington", "Kansas_Arkansas", "St. John's_Nebraska Omaha"], 
};

const nonUpsetsToIgnore: string [] = ["Louisville_Creighton", "Marquette_New Mexico", "Mississippi St._Baylor", 
  "Saint Mary's_Vanderbilt", "Gonzaga_Georgia", "UCLA_Utah St.", "Connecticut_Oklahoma", "Kansas_Arkansas"
]

const loadMatchups = () => {
  matchups.value = matchupFiles[selectedRegion.value] || [];
};

// Fetch and load selected matchup content
const loadMatchupContent = () => {
  if (!selectedMatchup.value) return;

  const team1 = selectedMatchup.value.split("_")[0];
  const team2 = selectedMatchup.value.split("_")[1];
  favLogo.value = `/madness/logos/${picMappings[team1]}`;
  dawgLogo.value = `/madness/logos/${picMappings[team2]}`;

  miFactor.value = upsetFactors[selectedMatchup.value].index;
  upsetChance.value = upsetFactors[selectedMatchup.value].upset;
  showFactors.value = true;
  showMethodology.value = false;
};

const closeMatchupContent = () => {
  showMethodology.value = true;
  showFactors.value = false;
  selectedMatchup.value = "";
  favLogo.value = "";
  dawgLogo.value = "";
};

</script>


<template>
  <div class="container mt-5">
    <div class="text-center mb-4">
      <img src="/public/bball.png" alt="Basketball" class="header-icon" />
      <h1 class="d-inline mx-3">MADNESS.IO</h1>
      <img src="/public/bball.png" alt="Basketball" class="header-icon" />
    </div>

    <!-- Region Selection -->
    <div class="d-flex justify-content-center mb-4">
      <select v-model="selectedRegion" @change="loadMatchups" class="form-select w-auto">
        <option value="" disabled>Select a Region</option>
        <option v-for="region in regions" :key="region" :value="region">
          {{ region }}
        </option>
      </select>
    </div>

    <!-- Matchup Selection (Shown After Region is Picked) -->
    <div v-if="matchups.length > 0" class="d-flex justify-content-center mb-4 ovr-banner">
      <img class="banner-pic" :src="favLogo" alt="" />
      <select v-model="selectedMatchup" @change="loadMatchupContent" class="form-select w-auto">
        <option value="" disabled>Select a Matchup</option>
        <option v-for="matchup in matchups" :key="matchup" :value="matchup">
          {{ matchup.replace("_", " vs. ") }}
        </option>
      </select>
      <img class="banner-pic" :src="dawgLogo" alt="" />
    </div>

    <div v-if="showFactors" class="d-flex justify-content-center mb-4 upset-factors">
      <h5 class="mi text-center"><strong>MADNESS INDEX: {{ miFactor }} / 10</strong></h5>
      <h5 class="factor text-center"><strong>Upset Chance: {{ upsetChance * 100 }}%</strong></h5>
    </div>

    <!-- Display Methodology Text -->
    <div v-if="showMethodology" class="mt-4 p-3 border border-secondary rounded bg-light">
      <p v-html="methodologyExplanation"></p>
    </div>

    <!-- Display Matchup Table -->
    <div v-if="currentMatchupData" class="mt-4 p-3 border border-secondary rounded bg-light position-relative">
      <button @click="closeMatchupContent" class="btn-close"></button>
      <UpsetTable v-if="currentUpsetData" :data="currentUpsetData" />
      <MatchupTable :data="currentMatchupData" />
    </div>

    <!-- Footer -->
    <footer class="text-center mt-5 text-muted">
      Contact: timthemoran@gmail.com
    </footer>
  </div>
</template>

<style scoped>
  body { background-color: #f8f9fa; }
  .container { margin-top: 30px; }
  .table { background-color: white; }
  th, td { text-align: center; }
  th.team-name { background-color: #888888; color: white; }

  .ovr-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;

    margin-top: -20px;
  }
  .form-select { height: 50px; }
  .banner-pic { 
    height: 90px; 
  }

  .upset-factors {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .mi {
    color: crimson;/* #DCA1A1;*/
  }

  .header-icon {
    height: 50px;
    width: 50px;
    margin-top: -22px;
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
    .banner-pic { 
      height: 40px; 
    }

    .ovr-banner {
      gap: 9px;
    }
  }

  @media only screen and (max-width: 100px) {
    .banner-pic { 
      height: 75px; 
    }
  }
</style>