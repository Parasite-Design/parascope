<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="map-container">
    <div class="page-header">
      <h1>Customers Map View</h1>
    </div>

    <div class="filters-section">
      <el-input
        v-model="departmentSearch"
        placeholder="Search by department (first 2 digits of code)"
        clearable
        style="width: 300px; margin-right: 15px"
        @clear="applyFilters"
        @keyup.enter="applyFilters"
      >
        <template #suffix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="favoriteFilter"
        placeholder="Favorite"
        clearable
        @change="applyFilters"
        style="width: 120px; margin-right: 15px"
      >
        <el-option label="Favorites" value="true" />
        <el-option label="Non-Favorites" value="false" />
      </el-select>

      <el-select
        v-model="activeFilter"
        placeholder="Active"
        clearable
        @change="applyFilters"
        style="width: 120px"
      >
        <el-option label="Active" value="true" />
        <el-option label="Inactive" value="false" />
      </el-select>

      <el-button
        type="primary"
        @click="showLegend = !showLegend"
        style="margin-left: 15px"
      >
        {{ showLegend ? "Hide" : "Show" }} Legend
      </el-button>
    </div>

    <div class="map-content">
      <!-- Map Legend -->
      <div v-if="showLegend" class="map-legend">
        <h4>Priority Score Legend</h4>
        <div class="legend-items">
          <div class="legend-item">
            <span class="legend-color high-priority"></span>
            <span>High Priority (≥ 5000)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color medium-priority"></span>
            <span>Medium Priority (1000-4999)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color low-priority"></span>
            <span>Low Priority (< 1000)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color no-score"></span>
            <span>No Score</span>
          </div>
        </div>
      </div>

      <!-- Map Container -->
      <div ref="mapContainer" class="map" v-loading="loading"></div>
    </div>

    <!-- Customer Detail Dialog -->
    <customer-detail
      v-model:visible="detailVisible"
      :customer="selectedCustomer"
      @customer-updated="fetchCustomers"
      @edit-customer="editCustomer"
    />

    <!-- Customer Edit Dialog -->
    <customer-edit
      v-model:visible="editVisible"
      :customer="editingCustomer"
      @customer-updated="fetchCustomers"
    />
  </div>
</template>

<script setup lang="ts">
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import CustomerDetail from "../components/CustomerDetail.vue";
import CustomerEdit from "../components/CustomerEdit.vue";
import { api } from "../stores/auth";
import { useSettingsStore } from "../stores/settings";

// Import Leaflet for mapping
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default markers in Leaflet with Webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface Customer {
  _id: string;
  code: string;
  city: string;
  latitude: string;
  longitude: string;
  name: string;
  phone: string;
  score: number;
  period1_total: number;
  period1_count: number;
  period2_total: number;
  objective: number;
  visits_count: number;
  favorite: boolean;
  active: boolean;
  period_progress: number;
  objective_progress: number;
  last_visit: string | null;
  next_visit: string | null;
  note?: string;
}

const settingsStore = useSettingsStore();

// Reactive data
const loading = ref(false);
const departmentSearch = ref("");
const favoriteFilter = ref("");
const activeFilter = ref("");
const showLegend = ref(true);

const detailVisible = ref(false);
const editVisible = ref(false);
const selectedCustomer = ref<Customer | null>(null);
const editingCustomer = ref<Customer | null>(null);

const allCustomers = ref<Customer[]>([]);
const filteredCustomers = ref<Customer[]>([]);

// Map references
const mapContainer = ref<HTMLElement>();
let map: L.Map | null = null;
let markers: L.LayerGroup | null = null;

// Color scheme for priority scores
const getMarkerColor = (score: number | undefined | null): string => {
  if (score === undefined || score === null) return "#909399"; // gray for no score

  if (score >= 5000) return "#f56c6c"; // red for high priority
  if (score >= 1000) return "#e6a23c"; // orange for medium priority
  return "#67c23a"; // green for low priority
};

const getMarkerSize = (score: number | undefined | null): number => {
  if (score === undefined || score === null) return 8;

  if (score >= 5000) return 12; // larger for high priority
  if (score >= 1000) return 10; // medium size for medium priority
  return 8; // smaller for low priority
};

const createCustomIcon = (customer: Customer) => {
  const color = getMarkerColor(customer.score);
  const size = getMarkerSize(customer.score);

  return L.divIcon({
    className: "custom-marker",
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer;
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const initializeMap = () => {
  if (!mapContainer.value) return;

  // Initialize map centered on France
  map = L.map(mapContainer.value).setView([46.603354, 1.888334], 6);

  // Add tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);

  // Initialize markers layer group
  markers = L.layerGroup().addTo(map);
};

const updateMapMarkers = () => {
  const currentMarkers = markers;
  if (!map || !currentMarkers) return;

  // Clear existing markers
  currentMarkers.clearLayers();

  // Add markers for filtered customers with valid coordinates
  filteredCustomers.value.forEach((customer) => {
    const lat = parseFloat(customer.latitude);
    const lng = parseFloat(customer.longitude);

    if (isNaN(lat) || isNaN(lng)) return;

    const marker = L.marker([lat, lng], {
      icon: createCustomIcon(customer),
    });

    // Tooltip on hover
    marker.bindTooltip(`
      <div class="customer-tooltip">
        <strong>${customer.name}</strong><br>
        <strong>Address:</strong> ${customer.city} (${customer.code})<br>
        <strong>Phone:</strong> ${customer.phone || "N/A"}<br>
        <strong>Last Visit:</strong> ${formatDate(customer.last_visit)}<br>
        <strong>Next Visit:</strong> ${formatDate(customer.next_visit)}<br>
        <strong>Units:</strong> ${customer.period1_count}
      </div>
    `);

    // Popup on click
    marker.bindPopup(`
      <div class="customer-popup">
        <h4>${customer.name}</h4>
        <p><strong>Code:</strong> ${customer.code}</p>
        <p><strong>City:</strong> ${customer.city}</p>
        <p><strong>Phone:</strong> ${customer.phone || "N/A"}</p>
        <p><strong>Last Visit:</strong> ${formatDate(customer.last_visit)}</p>
        <p><strong>Next Visit:</strong> ${formatDate(customer.next_visit)}</p>
        <p><strong>Units:</strong> ${customer.period1_count}</p>
        <p><strong>Priority Score:</strong> ${formatScore(customer.score)}</p>
        <p><strong>Status:</strong> ${customer.active ? "Active" : "Inactive"}</p>
        <button onclick="window.viewCustomerDetails('${customer._id}')" 
                style="margin-top: 10px; padding: 5px 10px; background: #409eff; color: white; border: none; border-radius: 4px; cursor: pointer;">
          View Details
        </button>
      </div>
    `);

    marker.on("click", () => {
      showCustomerDetails(customer);
    });

    currentMarkers.addLayer(marker);
  });

  // Fit map to show all markers
  if (filteredCustomers.value.length > 0) {
    const markerGroup = new L.FeatureGroup();
    currentMarkers.eachLayer((layer: any) => {
      markerGroup.addLayer(layer);
    });
    map.fitBounds(markerGroup.getBounds().pad(0.1));
  }
};

// Expose function to window for popup button
(window as any).viewCustomerDetails = (customerId: string) => {
  const customer = filteredCustomers.value.find((c) => c._id === customerId);
  if (customer) {
    showCustomerDetails(customer);
  }
};

const formatScore = (score: number | undefined | null) => {
  if (score === undefined || score === null) return "N/A";
  if (score >= 1000) {
    return `${(score / 1000).toFixed(1)}k`;
  }
  return Math.round(score).toString();
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString();
};

const fetchCustomers = async () => {
  loading.value = true;
  try {
    const period1Start = settingsStore.period.period_start;
    const period1End = settingsStore.period.period_end;

    const period1StartDate = new Date(period1Start);
    const period1EndDate = new Date(period1End);

    const period2Start = new Date(
      period1StartDate.getFullYear() - 1,
      period1StartDate.getMonth(),
      period1StartDate.getDate(),
    )
      .toISOString()
      .split("T")[0];
    const period2End = new Date(
      period1EndDate.getFullYear() - 1,
      period1EndDate.getMonth(),
      period1EndDate.getDate(),
    )
      .toISOString()
      .split("T")[0];

    const url = `/api/v1/customers/?period1_start=${period1Start}&period1_end=${period1End}&period2_start=${period2Start}&period2_end=${period2End}`;

    const response = await api.get(url);

    allCustomers.value = response.data;
    applyFilters();
  } catch (error) {
    console.error("Failed to fetch customers:", error);
    ElMessage.error("Failed to load customers");
  } finally {
    loading.value = false;
  }
};

const applyFilters = () => {
  let result = [...allCustomers.value];

  // Apply department filter
  if (departmentSearch.value) {
    result = result.filter(
      (customer) => customer.code.substring(0, 2) === departmentSearch.value,
    );
  }

  // Apply favorite filter
  if (favoriteFilter.value !== "") {
    const fav = favoriteFilter.value === "true";
    result = result.filter((customer) => customer.favorite === fav);
  }

  // Apply active filter
  if (activeFilter.value !== "") {
    const active = activeFilter.value === "true";
    result = result.filter((customer) => customer.active === active);
  }

  filteredCustomers.value = result;

  // Update map markers
  nextTick(() => {
    updateMapMarkers();
  });
};

watch([departmentSearch, favoriteFilter, activeFilter], () => {
  applyFilters();
});

const showCustomerDetails = (customer: Customer) => {
  selectedCustomer.value = customer;
  detailVisible.value = true;
};

const editCustomer = (customer: Customer) => {
  editingCustomer.value = { ...customer };
  editVisible.value = true;
};

onMounted(() => {
  initializeMap();
  fetchCustomers();
});

onUnmounted(() => {
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
.map-container {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filters-section {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
  align-items: center;
}

.map-content {
  flex: 1;
  display: flex;
  position: relative;
  gap: 20px;
}

.map-legend {
  position: absolute;
  top: 10px;
  right: 10px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
}

.legend-items {
  margin-top: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 8px;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.high-priority {
  background-color: #f56c6c;
}

.medium-priority {
  background-color: #e6a23c;
}

.low-priority {
  background-color: #67c23a;
}

.no-score {
  background-color: #909399;
}

.map {
  flex: 1;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Custom styles for Leaflet popups and tooltips */
:deep(.customer-tooltip) {
  font-size: 12px;
  line-height: 1.4;
}

:deep(.customer-popup) {
  min-width: 200px;
}

:deep(.customer-popup h4) {
  margin: 0 0 8px 0;
  color: #303133;
}

:deep(.customer-popup p) {
  margin: 4px 0;
  font-size: 13px;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
}

:deep(.custom-marker) {
  background: transparent !important;
  border: none !important;
}
</style>
