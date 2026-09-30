import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  { path: "/", name: "home", component: () => import("../views/HomeView.vue") },
  { path: "/listing/:slug", name: "detail", component: () => import("../views/DetailView.vue") },
  { path: "/landlord/:slug", name: "landlord", component: () => import("../views/LandlordView.vue") },
  { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
  { path: "/register", name: "register", component: () => import("../views/RegisterView.vue") },
  { path: "/publish", name: "publish", component: () => import("../views/PublishView.vue"), meta: { requiresAuth: true } },
  { path: "/my/listings", name: "myListings", component: () => import("../views/MyListingsView.vue"), meta: { requiresAuth: true } },
  { path: "/admin", name: "admin", component: () => import("../views/AdminView.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.token) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
  if (to.meta.requiresAdmin) {
    // 刷新页面时 user 可能还没 loadUser 完，先等一次再判定
    if (!auth.user) await auth.loadUser();
    if (!auth.user?.is_admin) return "/";
  }
});

export default router;
