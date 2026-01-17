<script setup lang="ts">
interface UpsetValue {
  value: string;
  color: string;
}

interface UpsetData {
  columns: string[];
  values: UpsetValue[];
}

defineProps<{
  data: UpsetData;
}>();
</script>

<template>
  <div class="container">
    <h2 class="text-center">Upset Factors</h2>
    <h6 class="text-center"><em>Upset Correlation out of 10</em></h6>
    <div class="table-responsive">
      <table class="table table-bordered table-striped">
        <thead>
          <tr class="text-center">
            <th 
              v-for="(column, index) in data.columns" 
              :key="index"
              style="background-color: #ffffff; color: #000000"
            >
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr class="text-center">
            <td 
              v-for="(item, index) in data.values" 
              :key="index"
              :style="{ backgroundColor: item.color }"
            >
              {{ item.value }}
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
</style>
