import axios from "axios";
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Login from "../views/Login.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: Login,
      meta: { requiresAuth: false },
    },
    {
      path: "/",
      name: "dashboard",
      component: () => import("../views/Statistics.vue"),
      meta: { requiresAuth: true },
    },
    // router/index.ts
    {
      path: "/prospects",
      name: "prospects",
      component: () => import("../views/Prospects.vue"),
      meta: { requiresAuth: true },
    },
    // router/index.ts
    {
      path: "/customers",
      name: "customers",
      component: () => import("../views/Customers.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/products",
      name: "products",
      component: () => import("../views/Products.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/models",
      name: "models",
      component: () => import("../views/Models.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/map",
      name: "map",
      component: () => import("../views/Map.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/settings/brands",
      name: "brand",
      component: () => import("../views/Brand.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/settings/objective",
      name: "objective",
      component: () => import("../views/Objective.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/account",
      name: "account",
      component: () => import("../views/Account.vue"),
      meta: { requiresAuth: true },
    },
    // ... other routes
  ],
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth) {
    if (!authStore.token) {
      next("/login");
      return;
    }

    try {
      await axios.get("/api/v1/validate");
      next();
    } catch (error) {
      // Type guard to check if it's an AxiosError
      if (axios.isAxiosError(error)) {
        // Now TypeScript knows this is an AxiosError
        if (error.response?.status === 401) {
          await authStore.logout();
          next("/login");
        } else {
          console.error("Validation error:", error);
          next();
        }
      } else {
        // Handle non-Axios errors
        console.error("Unexpected error:", error);
        next("/login");
      }
    }
  } else {
    next();
  }
});

export default router;
