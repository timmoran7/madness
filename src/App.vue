<script setup lang="ts">
import { ref } from "vue";

const regions = ["South", "East", "Midwest", "West"];
const selectedRegion = ref<string>("");
const matchups = ref<string[]>([]);
const selectedMatchup = ref<string>("");
const matchupContent = ref<string>("");
const upsetContent = ref<string>("");
const favLogo = ref<string>("");
const dawgLogo = ref<string>("");

const nameMappings: { [key: string]: string } = {
  "Wisconsin": "wisconsin.svg",
  "Utah St.": "utah-st.svg",
  "Arkansas": "arkansas.svg",
  "Texas": "texas.svg",
  "Kansas": "kansas.svg",
  "High Point": "high-point.svg",
  "McNeese": "mcneese.svg",
  "Texas A&M": "texas-am.svg",
  "Purdue": "purdue.svg",
  "SIUE": "siu-edwardsville.svg",
  "Nebraska Omaha": "neb-omaha.svg",
  "Georgia": "georgia.svg",
  "UCLA": "ucla.svg",
  "Baylor": "baylor.svg",
  "New Mexico": "new-mexico.svg",
  "Michigan St.": "michigan-st.svg",
  "UNC Wilmington": "unc-wilmington.svg",
  "Oregon": "oregon.svg",
  "Kentucky": "kentucky.svg",
  "Colorado St.": "colorado-st.svg",
  "Louisville": "louisville.svg",
  "Bryant": "bryant.svg",
  "Lipscomb": "lipscomb.svg",
  "Clemson": "clemson.svg",
  "Akron": "akron.svg",
  "Oklahoma": "oklahoma.svg",
  "Auburn": "auburn.svg",
  "Florida": "florida.svg",
  "Tennessee": "tennessee.svg",
  "Montana": "montana.svg",
  "Yale": "yale.svg",
  "Xavier": "xavier.svg",
  "Marquette": "marquette.svg",
  "Norfolk St.": "norfolk-st.svg",
  "Creighton": "creighton.svg",
  "Mississippi": "mississippi-st.svg",
  "Maryland": "maryland.svg",
  "VCU": "vcu.svg",
  "Troy": "troy.svg",
  "Arizona": "arizona.svg",
  "Illinois": "illinois.svg",
  "Liberty": "liberty.svg",
  "Houston": "houston.svg",
  "BYU": "byu.svg",
  "Saint Mary's": "st-marys-ca.svg",
  "Vanderbilt": "vanderbilt.svg",
  "Memphis": "memphis.svg",
  "Robert Morris": "robert-morris.svg",
  "Alabama": "alabama.svg",
  "Missouri": "missouri.svg",
  "St. John's": "st-johns-ny.svg",
  "Texas Tech": "texas-tech.svg",
  "Mississippi St.": "mississippi-st.svg",
  "Duke": "duke.svg",
  "Michigan": "michigan.svg",
  "Connecticut": "uconn.svg",
  "Drake": "drake.svg",
  "North Carolina": "north-carolina.svg",
  "Grand Canyon": "grand-canyon.svg",
  "Saint Francis": "st-francis-pa.svg",
  "UC San Diego": "uc-san-diego.svg",
  "San Diego St.": "san-diego-st.svg",
  "Iowa St.": "iowa-st.svg",
  "American": "american.svg",
  "Gonzaga": "gonzaga.svg",
  "Wofford": "wofford.svg",
  "Alabama St.": "alabama-st.svg",
  "Mount St. Mary's": "mt-st-marys.svg"
};

// Replace this with actual matchup filenames
const matchupFiles: { [key: string]: string[] } = {
  South: ["Auburn_Alabama St.", "Louisville_Creighton", "Auburn_Saint Francis", "Michigan_UC San Diego", "Texas A&M_Yale", "Mississippi_North Carolina", 
    "Mississippi_San Diego St.", "Iowa St._Lipscomb", "Marquette_New Mexico", "Michigan St._Bryant"],
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
  selectedMatchup.value = ""; // Reset selected matchup
  matchupContent.value = ""; // Clear displayed content

  upsetContent.value = ""; // Clear displayed content
};

// Fetch and load selected matchup content
const loadMatchupContent = async () => {
  if (!selectedMatchup.value) return;
  try {
    const response = await fetch(`/madness/matchups/${selectedMatchup.value}.html`);
    matchupContent.value = await response.text();
    favLogo.value = `/madness/logos/${nameMappings[selectedMatchup.value.split("_")[0]]}`;
    dawgLogo.value = `/madness/logos/${nameMappings[selectedMatchup.value.split("_")[1]]}`;
  } catch (error) {
    matchupContent.value = "<p class='text-danger'>Error loading matchup.</p>";
  }

  if(nonUpsetsToIgnore.includes(selectedMatchup.value)){
    upsetContent.value = "";
    return;
  } 
  try {
    const response = await fetch(`/madness/upsets/${selectedMatchup.value}.html`);
    upsetContent.value = await response.text();
  } catch (error) {
    upsetContent.value = "<p class='text-danger'>Error loading matchup.</p>";
  }
};

</script>


<template>
  <div class="container mt-5">
    <h1 class="text-center mb-4">MADNESS.IO</h1>

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

    <!-- Display Matchup Table -->
    <div v-if="matchupContent" class="mt-4 p-3 border border-secondary rounded bg-light">
      <div v-html="upsetContent"></div>
      <div v-html="matchupContent"></div>
    </div>
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
  .banner-pic { height: 100px; }
</style>