<template>
  <div class="home-container">
    <h1>Welcome to the Dashboard</h1>
    <p>User: {{ authStore.user?.email }}</p>
    <p v-if="authStore.user?.is_admin" class="admin-badge">
      <el-tag type="success">Administrator</el-tag>
    </p>

    <div class="current-settings">
      <h3>Current Settings</h3>
      <p>
        <strong>Selected Brand:</strong>
        {{ selectedBrandName || "None selected" }}
      </p>
      <p>
        <strong>Period Type:</strong>
        {{ periodTypeLabel }}
      </p>
      <p>
        <strong>Period Range:</strong>
        {{ formatDate(settingsStore.period.period_start) }} to
        {{ formatDate(settingsStore.period.period_end) }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "../stores/auth";
import { useSettingsStore } from "../stores/settings";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();

const selectedBrandName = computed(() => {
  const brand = settingsStore.brands.find(
    (b) => b.brand_name === settingsStore.selectedBrand
  );
  return brand ? brand.showed_brand_name : "";
});

const periodTypeLabel = computed(() => {
  switch (settingsStore.selectedPeriodType) {
    case "fiscal":
      return "Fiscal Year";
    case "rolling":
      return "Rolling Year";
    case "custom":
      return "Custom Period";
    default:
      return "Not set";
  }
});

const formatDate = (dateString: string) => {
  if (!dateString) return "Not set";
  return new Date(dateString).toLocaleDateString();
};
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.current-settings {
  margin-top: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.admin-badge {
  margin-top: -10px;
  margin-bottom: 20px;
}
</style>
