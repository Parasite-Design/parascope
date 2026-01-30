<template>
  <div
    class="sidebar-container"
    :class="{ collapsed: uiStore.isSidebarCollapsed }"
  >
    <el-scrollbar class="sidebar-scrollbar">
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :collapse="uiStore.isSidebarCollapsed"
        background-color="#344a5f"
        text-color="#b7c0cd"
        active-text-color="#409EFF"
        router
      >
        <!-- Dashboard -->
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>

        <!-- Prospects -->
        <el-menu-item index="/prospects">
          <el-icon><User /></el-icon>
          <template #title>
            <span>Prospects</span>
          </template>
        </el-menu-item>

        <!-- Customers -->
        <el-menu-item index="/customers">
          <el-icon><Avatar /></el-icon>
          <template #title>
            <span>Customers</span>
          </template>
        </el-menu-item>

        <!-- Products -->
        <el-menu-item index="/products">
          <el-icon><ShoppingBag /></el-icon>
          <template #title>Products</template>
        </el-menu-item>

        <!-- Models -->
        <el-menu-item index="/models">
          <el-icon><Box /></el-icon>
          <template #title>Colors</template>
        </el-menu-item>

        <!-- Models -->
        <el-menu-item index="/map">
          <el-icon><Box /></el-icon>
          <template #title>Map</template>
        </el-menu-item>

        <el-menu-item index="/account">
          <el-icon><Lock /></el-icon>
          <template #title>Account</template>
        </el-menu-item>

        <!-- Settings -->
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>Settings</span>
          </template>
          <el-menu-item index="/settings/brands">Brand Management</el-menu-item>
          <el-menu-item index="/settings/objective"
            >Update Objective</el-menu-item
          >
        </el-sub-menu>
      </el-menu>
    </el-scrollbar>

    <div class="sidebar-footer" @click="uiStore.toggleSidebar">
      <el-icon :class="{ 'rotate-180': uiStore.isSidebarCollapsed }">
        <ArrowLeft />
      </el-icon>
      <span v-if="!uiStore.isSidebarCollapsed">Collapse</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowLeft,
  Avatar,
  Box,
  House,
  Lock,
  ShoppingBag,
  User,
} from "@element-plus/icons-vue";
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useUIStore } from "../stores/ui";

const route = useRoute();
const uiStore = useUIStore();

const activeMenu = computed(() => {
  return route.path;
});
</script>

<style scoped>
.sidebar-container {
  position: fixed;
  top: 60px;
  left: 0;
  bottom: 0;
  width: 240px;
  background-color: #344a5f;
  transition: width 0.3s ease;
  z-index: 900;
  display: flex;
  flex-direction: column;
}

.sidebar-container.collapsed {
  width: 64px;
}

.sidebar-scrollbar {
  flex: 1;
}

.sidebar-menu {
  border: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 240px;
}

.sidebar-footer {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 20px;
  color: #b7c0cd;
  cursor: pointer;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  transition: background-color 0.3s;
}

.sidebar-footer:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.sidebar-footer span {
  margin-left: 10px;
  font-size: 14px;
}

.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.3s;
}
</style>
