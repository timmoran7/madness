import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import MatchupPage from "@/pages/MatchupPage.vue";
import TeamRoutePage from "@/pages/TeamRoutePage.vue";

const isGitHubPages =
  typeof window !== "undefined" && window.location.hostname.endsWith("github.io");

const router = createRouter({
  history: isGitHubPages
    ? createWebHashHistory(import.meta.env.BASE_URL)
    : createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "matchup",
      component: MatchupPage,
    },
    {
      path: "/:teamName",
      name: "team",
      component: TeamRoutePage,
      props: true,
    },
  ],
});

export default router;
