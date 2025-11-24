import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { requiresAuth: true }
    },
    // router/index.ts
    {
      path: '/prospects',
      name: 'prospects',
      component: () => import('../views/Prospects.vue'),
      meta: { requiresAuth: true }
    },
    // router/index.ts
    {
      path: '/customers',
      name: 'customers',
      component: () => import('../views/Customers.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/products',
      name: 'products',
      component: () => import('../views/Products.vue'),
      meta: { requiresAuth: true }
    }
    // ... other routes
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated()) {
    // Only redirect to login, don't call logout
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.user?.is_admin) {
    // Redirect to home if not admin, don't call logout
    next('/')
  } else {
    next()
  }
})

export default router