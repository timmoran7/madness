<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import TeamPage from "@/components/TeamPage.vue";
import pictureMappings from "@/data/picMappings.json";
import rawKpStats from "@/data/kpOvrStats2025.json";
import rawQuadStats from "@/data/quadStats2025.json";

const route = useRoute();

type KpStatPair = Array<string | number | null>;
type KpTeamStats = Record<string, KpStatPair>;
const kpStatsData = rawKpStats as Record<string, KpTeamStats>;

interface QuadBucket {
  record: string;
  games: string[];
}

interface TeamQuadResults {
  q1: QuadBucket;
  q2: QuadBucket;
  q3: QuadBucket;
  q4: QuadBucket;
}

interface TeamStatDetail {
  rank: string;
  value: string;
}

const EMPTY_QUAD_BUCKET: QuadBucket = {
  record: "0-0",
  games: [],
};

const quadStatsData = rawQuadStats as Record<string, TeamQuadResults>;
const picMappings: { [key: string]: string } = pictureMappings;

const teamName = computed<string>(() => {
  const rawName = route.params.teamName;
  return typeof rawName === "string" ? decodeURIComponent(rawName) : "";
});

const teamLogo = computed<string>(() => {
  const fileName = picMappings[teamName.value];
  return fileName ? `/madness/logos/${fileName}` : "";
});

const teamPageStats = computed(() => {
  const teamStats = kpStatsData[teamName.value];
  if (!teamStats) {
    return null;
  }

  const readStat = (label: string): string => {
    const value = teamStats[label]?.[1];
    return value === undefined || value === null ? "N/A" : String(value);
  };

  const readRank = (label: string): string => {
    const value = teamStats[label]?.[0];
    return value === undefined || value === null ? "N/A" : String(value);
  };

  const readStatDetail = (label: string): TeamStatDetail => {
    return {
      rank: readRank(label),
      value: readStat(label),
    };
  };

  return {
    overallRank: readRank("KenPom Ovr."),
    record: readStat("KenPom Ovr."),
    offEfficiency: readStatDetail("Off Efficiency"),
    defEfficiency: readStatDetail("Def Efficiency"),
    height: readStatDetail("Average Height"),
    continuity: readStatDetail("Minutes Continuity"),
    experience: readStatDetail("D-1 Experience"),
    benchMinutes: readStatDetail("Bench Minutes"),
    sosOverall: readStatDetail("SOS Overall"),
    sosNonConference: readStatDetail("SOS Non-conference"),
  };
});

const teamQuadResults = computed<TeamQuadResults>(() => {
  return (
    quadStatsData[teamName.value] ?? {
      q1: EMPTY_QUAD_BUCKET,
      q2: EMPTY_QUAD_BUCKET,
      q3: EMPTY_QUAD_BUCKET,
      q4: EMPTY_QUAD_BUCKET,
    }
  );
});
</script>

<template>
  <div class="container mt-5">
    <TeamPage
      v-if="teamPageStats"
      :team-name="teamName"
      :team-logo="teamLogo"
      game-log-image="/madness/gameLogs/image.png"
      :stats="teamPageStats"
      :quads="teamQuadResults"
    />

    <div v-else class="mt-4 p-3 border border-secondary rounded bg-light text-center">
      <h3 class="mb-2">Team not found</h3>
      <p class="text-muted mb-0">No team page data is available for this route.</p>
    </div>
  </div>
</template>
