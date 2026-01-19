import axios from 'axios'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/Statistics.vue'),
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
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/Models.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('../views/Map.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings/brands',
      name: 'brand',
      component: () => import('../views/Brand.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/settings/objective',
      name: 'objective',
      component: () => import('../views/Objective.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('../views/Account.vue'),
      meta: { requiresAuth: true }
    }
    // ... other routes
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth) {
    // Check if we have a token
    if (!authStore.token) {
      next('/login')
      return
    }
    
    // Use the API to validate token
    // The interceptor will handle refresh automatically
    try {
      // Use your existing axios instance (api) which has the interceptor
      await axios.get('/api/v1/validate')
      next()
    } catch (error) {
      // If error is still 401 after interceptor tried to refresh, logout
      if (error.response?.status === 401) {
        await authStore.logout()
        next('/login')
      } else {
        // For other errors, you might want to handle differently
        console.error('Validation error:', error)
        next() // Or handle error appropriately
      }
    }
  } else {
    next()
  }
})

export default router