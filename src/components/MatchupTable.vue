<script setup lang="ts">
interface Stat {
  value: string;
  color: string;
}

interface Team {
  name: string;
  stats: Stat[];
}

interface MatchupData {
  columns: string[];
  teams: Team[];
}

defineProps<{
  data: MatchupData;
}>();
</script>

<template>
  <div class="container">
    <h2 class="text-center">All Stats</h2> 
    <h6 class="text-center"><em>Rank of all 364 NCAAB D1 teams</em></h6>
    <div class="table-responsive">
      <table class="table table-bordered table-striped">
        <thead class="text-center">
          <tr>
            <th class="team-name">Team</th>
            <th v-for="(column, index) in data.columns" :key="index">{{ column }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(team, teamIndex) in data.teams" :key="teamIndex" class="text-center">
            <td class="team-name">{{ team.name }}</td>
            <td 
              v-for="(stat, statIndex) in team.stats" 
              :key="statIndex"
              :style="{ backgroundColor: stat.color }"
            >
              {{ stat.value }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table { 
  background-color: white; 
}

th, td { 
  text-align: center; 
}

th.team-name { 
  background-color: #888888; 
  color: white; 
}
</style>
