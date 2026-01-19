<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-button
        @click="uiStore.toggleSidebar"
        :icon="Menu"
        circle
        class="sidebar-toggle"
      />
      <h2>I-VISION</h2>
    </div>
    <div class="header-right">
      <span class="user-info">{{ selectedBrandName }}</span>
      <el-button @click="settingsDrawer = true" :icon="Setting" circle />
      <el-button @click="handleLogout" :icon="SwitchButton" circle />
    </div>

    <!-- Settings Drawer -->
    <el-drawer
      v-model="settingsDrawer"
      title="Settings"
      :before-close="handleDrawerClose"
      size="400px"
    >
      <div class="settings-content">
        <!-- Brand Selection -->
        <div class="settings-section">
          <h3>Brand Selection</h3>
          <el-select
            v-model="settingsStore.selectedBrand"
            placeholder="Select a brand"
            @change="settingsStore.setBrand"
            style="width: 100%"
          >
            <!-- Add "All Brands" option -->
            <el-option label="All Brands" value="" />
            <el-option
              v-for="brand in settingsStore.brands"
              :key="brand.brand_name"
              :label="brand.showed_brand_name"
              :value="brand.brand_name"
            />
          </el-select>
        </div>

        <!-- Period Selection -->
        <div class="settings-section">
          <h3>Period Selection</h3>
          <el-radio-group
            v-model="selectedPeriodType"
            @change="handlePeriodChange"
            class="period-options"
          >
            <el-radio label="fiscal">Fiscal Year</el-radio>
            <el-radio label="rolling">Rolling Year</el-radio>
            <el-radio label="custom">Custom Period</el-radio>
          </el-radio-group>

          <div v-if="selectedPeriodType === 'custom'" class="custom-period">
            <el-date-picker
              v-model="customPeriodRange"
              type="daterange"
              range-separator="To"
              start-placeholder="Start date"
              end-placeholder="End date"
              value-format="YYYY-MM-DD"
              style="width: 100%; margin-top: 10px"
            />
            <el-button
              type="primary"
              @click="applyCustomPeriod"
              style="margin-top: 10px"
            >
              Apply Custom Period
            </el-button>
          </div>

          <div v-else class="period-display">
            <p><strong>Current Period:</strong></p>
            <p>
              {{ formatDate(settingsStore.period.period_start) }} to
              {{ formatDate(settingsStore.period.period_end) }}
            </p>
          </div>
        </div>
      </div>
    </el-drawer>
  </el-header>
</template>

<script setup lang="ts">
import { Menu, Setting, SwitchButton } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useSettingsStore } from "../stores/settings";
import { useUIStore } from "../stores/ui";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const uiStore = useUIStore();
const router = useRouter();

const settingsDrawer = ref(false);
const selectedPeriodType = ref(settingsStore.selectedPeriodType);
const customPeriodRange = ref<[string, string]>(["", ""]);

onMounted(() => {
  settingsStore.initialize();
});

const handleLogout = () => {
  authStore.logout();
  router.push("/login");
};

const handleDrawerClose = (done: () => void) => {
  done();
};

const handlePeriodChange = (type: string) => {
  if (type !== "custom") {
    settingsStore.fetchPeriod(type);
  }
};

const applyCustomPeriod = () => {
  if (customPeriodRange.value && customPeriodRange.value.length === 2) {
    const [start, end] = customPeriodRange.value;
    settingsStore.setCustomPeriod(start, end);
    ElMessage.success("Custom period applied successfully");
  } else {
    ElMessage.error("Please select a valid date range");
  }
};

const formatDate = (dateString: string) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleDateString();
};

const selectedBrandName = computed(() => {
  const brand = settingsStore.brands.find(
    (b) => b.brand_name === settingsStore.selectedBrand
  );
  return brand ? brand.showed_brand_name : "";
});

</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #2c3e50;
  color: white;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 60px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
  color: white;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  margin-right: 10px;
  font-size: 14px;
}

.sidebar-toggle {
  background-color: transparent;
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.sidebar-toggle:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.settings-content {
  padding: 0 20px;
}

.settings-section {
  margin-bottom: 30px;
}

.settings-section h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.period-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.period-display {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.period-display p {
  margin: 5px 0;
}

.custom-period {
  margin-top: 15px;
}
</style>
