import { createRouter, createWebHistory } from "vue-router";
import MatchupPage from "@/pages/MatchupPage.vue";
import TeamRoutePage from "@/pages/TeamRoutePage.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
