<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import TeamPage from "@/components/TeamPage.vue";
import teamLogoUrlsData from "@/data/teamLogoUrls.json";
import rawKpGames from "@/data/kpGames2026.json";
import rawKpStats from "@/data/kpOvrStats2026.json";
import rawQuadStats from "@/data/quadStats2026.json";

const route = useRoute();

type KpStatPair = Array<string | number | null>;
type KpStatValue = KpStatPair | string | number | null;
type KpTeamStats = Record<string, KpStatValue>;
const kpStatsData = rawKpStats as Record<string, KpTeamStats>;

interface QuadBucket {
  record: string;
  games: string[];
}

interface TeamQuadResults {
  net?: string;
  q1: QuadBucket;
  q2: QuadBucket;
  q3: QuadBucket;
  q4: QuadBucket;
}

interface TeamStatDetail {
  rank: string;
  value: string;
}

interface TeamPageStatRow extends TeamStatDetail {
  label: string;
}

interface TeamGameRow {
  date: string;
  opponentRank: string;
  opponent: string;
  result: string;
  location: string;
  record: string;
  conferenceRecord: string;
}

const EMPTY_QUAD_BUCKET: QuadBucket = {
  record: "0-0",
  games: [],
};

const kpGamesData = rawKpGames as { teams: Record<string, TeamGameRow[]> };
const quadStatsData = rawQuadStats as Record<string, TeamQuadResults>;
const teamLogoUrls: Record<string, string> = teamLogoUrlsData;

const normalizeTeamName = (name: string): string =>
  name
    .toLowerCase()
    .replace(/\./g, "")
    .replace(/'/g, "")
    .replace(/&/g, "and")
    .replace(/\s+/g, " ")
    .trim();

const kpGamesKeysByNormalizedName = new Map(
  Object.keys(kpGamesData.teams).map((team) => [normalizeTeamName(team), team]),
);

const resolveKpGamesTeamName = (candidate: string): string | null => {
  if (kpGamesData.teams[candidate]) {
    return candidate;
  }

  return kpGamesKeysByNormalizedName.get(normalizeTeamName(candidate)) ?? null;
};

const teamName = computed<string>(() => {
  const rawName = route.params.teamName;
  return typeof rawName === "string" ? decodeURIComponent(rawName) : "";
});

const teamLogo = computed<string>(() => {
  return teamLogoUrls[teamName.value] ?? "";
});

const teamPageStats = computed(() => {
  const teamStats = kpStatsData[teamName.value];
  if (!teamStats) {
    return null;
  }

  const readStat = (label: string): string => {
    const stat = teamStats[label];
    const value = Array.isArray(stat) ? stat[1] : undefined;
    return value === undefined || value === null ? "N/A" : String(value);
  };

  const readRank = (label: string): string => {
    const stat = teamStats[label];
    const value = Array.isArray(stat) ? stat[0] : undefined;
    return value === undefined || value === null ? "N/A" : String(value);
  };

  const readStatDetail = (label: string): TeamStatDetail => {
    return {
      rank: readRank(label),
      value: readStat(label),
    };
  };

  const fieldsToNotDisplay = ["KenPom Ovr.", "seed", "conference", "Off Avg. Poss. Length"];
  const rankRatingStats: TeamPageStatRow[] = Object.entries(teamStats)
    .filter(([label, stat]) => {
      if (fieldsToNotDisplay.includes(label)) {
        return false;
      }

      return Array.isArray(stat);
    })
    .map(([label]) => ({
      label,
      ...readStatDetail(label),
    }));

  return {
    overallRank: readRank("KenPom Ovr."),
    record: readStat("KenPom Ovr."),
    netRank: quadStatsData[teamName.value]?.net ?? "N/A",
    rankRatingStats,
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

const teamGameLog = computed<TeamGameRow[]>(() => {
  const resolvedTeamName = resolveKpGamesTeamName(teamName.value);
  if (!resolvedTeamName) {
    return [];
  }

  return kpGamesData.teams[resolvedTeamName] ?? [];
});
</script>

<template>
  <div class="container mt-5">
    <TeamPage
      v-if="teamPageStats"
      :team-name="teamName"
      :team-logo="teamLogo"
      :game-log="teamGameLog"
      :stats="teamPageStats"
      :quads="teamQuadResults"
    />

    <div v-else class="mt-4 p-3 border border-secondary rounded bg-light text-center">
      <h3 class="mb-2">Team not found</h3>
      <p class="text-muted mb-0">No team page data is available for this route.</p>
    </div>
  </div>
</template>
