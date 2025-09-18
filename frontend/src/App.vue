<template>
  <div id="app">
    <!-- Remove <auth-handler /> -->
    <app-header v-if="showHeader" />
    <div class="main-container" v-if="showHeader">
      <app-sidebar />
      <main class="main-content" :class="{ 'sidebar-collapsed': uiStore.isSidebarCollapsed }">
        <router-view />
      </main>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import { useUIStore } from './stores/ui'

const route = useRoute()
const uiStore = useUIStore()

const showHeader = computed(() => route.name !== 'login')
</script>

<style>
#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

body {
  margin: 0;
  padding: 0;
  background-color: #f5f7fa;
}

.main-container {
  display: flex;
  min-height: 100vh;
  padding-top: 60px; /* Header height */
}

.main-content {
  flex: 1;
  padding: 20px;
  margin-left: 240px; /* Sidebar width */
  transition: margin-left 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: 64px; /* Collapsed sidebar width */
}

/* Custom scrollbar for the entire app */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>