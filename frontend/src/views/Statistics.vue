<template>
  <div class="statistics-container">
    <div class="page-header">
      <h1>Performance Statistics</h1>
      <div class="period-display">
        <span class="period-label">Viewing period:</span>
        <span class="period-dates">{{ formattedPeriod }}</span>
      </div>
    </div>

    <!-- Filters Card -->
    <el-card class="filters-card">
      <template #header>
        <div class="card-header">
          <span>Data Filters</span>
        </div>
      </template>
      <div class="filters-content">
        <div class="filter-row">
          <div class="filter-item">
            <span class="filter-label">Time Period:</span>
            <el-tag type="info" size="large">
              {{ settingsStore.period.period_start }} to {{ settingsStore.period.period_end }}
            </el-tag>
            <span class="filter-help">Set in global settings</span>
          </div>
          <div class="filter-item">
            <span class="filter-label">Selected Brand:</span>
            <el-tag v-if="settingsStore.selectedBrand" type="primary" size="large">
              {{ getBrandDisplayName(settingsStore.selectedBrand) }}
            </el-tag>
            <el-tag v-else type="info" size="large">
              All Brands
            </el-tag>
          </div>
        </div>
        <div class="data-status">
          <el-alert 
            v-if="fetchError" 
            :title="fetchError" 
            type="error" 
            :closable="false"
            show-icon
          />
          <div v-else-if="loading" class="loading-state">
            <el-icon class="is-loading" size="24"><Loading /></el-icon>
            <span>Loading statistics data...</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Objectives Info Card -->
    <el-card v-if="objectivesInfo" class="objectives-info-card">
      <template #header>
        <div class="card-header">
          <span>Current Objectives</span>
        </div>
      </template>
      <div class="objectives-content">
        <div v-if="!hasObjectives" class="no-objectives">
          <el-empty description="No objectives set for this context" />
        </div>
        <div v-else class="objectives-list">
          <div class="objective-item">
            <span class="objective-label">Sales per Customer:</span>
            <span class="objective-value">
              {{ formatCurrency(salesPerCustomerObjective) }}
              <span class="objective-context">({{ objectiveBrandContext }})</span>
            </span>
          </div>
          <div class="objective-item">
            <span class="objective-label">Active Customers:</span>
            <span class="objective-value">
              {{ activeCustomersObjective.toLocaleString() }}
              <span class="objective-context">({{ objectiveBrandContext }})</span>
            </span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Main Statistics Dashboard -->
    <div class="statistics-grid">
      <!-- Sales Performance -->
      <el-card class="stat-card sales-card">
        <template #header>
          <div class="card-header">
            <span>Sales Performance</span>
            <el-tag :type="salesProgressType" size="small">
              {{ salesProgressPercentage }}% of target
            </el-tag>
          </div>
        </template>
        <div class="stat-content">
          <div class="stat-main">
            <div class="stat-value">{{ formatCurrency(statsData.sales) }}</div>
            <div class="stat-label">Total Sales</div>
          </div>
          <div v-if="hasSalesObjective" class="stat-comparison">
            <div class="comparison-item">
              <span class="comparison-label">Objective:</span>
              <span class="comparison-value">{{ formatCurrency(salesObjective) }}</span>
            </div>
            <div class="comparison-item">
              <span class="comparison-label">Remaining:</span>
              <span class="comparison-value" :class="salesRemainingClass">
                {{ formatCurrency(salesRemaining) }}
              </span>
            </div>
          </div>
          <div v-else class="stat-help">
            <el-icon><InfoFilled /></el-icon>
            <span>Sales objective not set for {{ objectiveBrandContext }}</span>
          </div>
        </div>
      </el-card>

      <!-- Units Sold -->
      <el-card class="stat-card units-card">
        <template #header>
          <div class="card-header">
            <span>Units Sold</span>
          </div>
        </template>
        <div class="stat-content">
          <div class="stat-main">
            <div class="stat-value">{{ statsData.units.toLocaleString() }}</div>
            <div class="stat-label">Total Units</div>
          </div>
          <div class="stat-details">
            <div class="detail-item">
              <span class="detail-label">Average Price:</span>
              <span class="detail-value">{{ formatCurrency(statsData.average_price) }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Sales Channels -->
      <el-card class="stat-card channels-card">
        <template #header>
          <div class="card-header">
            <span>Sales Channels</span>
          </div>
        </template>
        <div class="stat-content">
          <div class="channel-row">
            <div class="channel-item">
              <div class="channel-value">{{ formatCurrency(statsData.web_sales) }}</div>
              <div class="channel-label">Web Sales</div>
              <div class="channel-percentage">
                {{ calculatePercentage(statsData.web_sales, statsData.sales) }}%
              </div>
            </div>
            <div class="channel-item">
              <div class="channel-value">{{ formatCurrency(statsData.direct_sales) }}</div>
              <div class="channel-label">Direct Sales</div>
              <div class="channel-percentage">
                {{ calculatePercentage(statsData.direct_sales, statsData.sales) }}%
              </div>
            </div>
          </div>
          <div class="channel-row">
            <div class="channel-item returns-item">
              <div class="channel-value" :class="{ 'negative': statsData.return < 0 }">
                {{ formatCurrency(statsData.return) }}
              </div>
              <div class="channel-label">Returns</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Customer Metrics -->
      <el-card class="stat-card customers-card">
        <template #header>
          <div class="card-header">
            <span>Customer Metrics</span>
            <el-tag :type="customersProgressType" size="small">
              {{ customersProgressPercentage }}% of target
            </el-tag>
          </div>
        </template>
        <div class="stat-content">
          <div class="customer-main">
            <div class="customer-group">
              <div class="customer-value">{{ statsData.customers.toLocaleString() }}</div>
              <div class="customer-label">Total Customers</div>
            </div>
            <div class="customer-group">
              <div class="customer-value">{{ statsData.active_customers.toLocaleString() }}</div>
              <div class="customer-label">Active Customers</div>
            </div>
          </div>
          <div v-if="hasActiveCustomersObjective" class="stat-comparison">
            <div class="comparison-item">
              <span class="comparison-label">Objective:</span>
              <span class="comparison-value">{{ activeCustomersObjective.toLocaleString() }}</span>
            </div>
            <div class="comparison-item">
              <span class="comparison-label">Remaining:</span>
              <span class="comparison-value" :class="customersRemainingClass">
                {{ customersRemaining.toLocaleString() }}
              </span>
            </div>
          </div>
          <div v-else class="stat-help">
            <el-icon><InfoFilled /></el-icon>
            <span>Active customers objective not set for {{ objectiveBrandContext }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { InfoFilled, Loading } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

interface StatisticsData {
  sales: number
  units: number
  web_sales: number
  direct_sales: number
  return: number
  average_price: number
  customers: number
  active_customers: number
}

interface RepresentativeData {
  id: string
  code: number
  key: string
  name: string
  objectives: Record<string, Record<string, number>>
}

interface Brand {
  brand_name: string
  showed_brand_name: string
}

const authStore = useAuthStore()
const settingsStore = useSettingsStore()

// State
const statsData = reactive<StatisticsData>({
  sales: 0,
  units: 0,
  web_sales: 0,
  direct_sales: 0,
  return: 0,
  average_price: 0,
  customers: 0,
  active_customers: 0
})

const brands = ref<Brand[]>([])
const representativeData = ref<RepresentativeData | null>(null)
const loading = ref(false)
const fetchError = ref<string | null>(null)

// Fetch data on component mount and when settings change
onMounted(() => {
  fetchAllData()
})

// Watch for changes in settings
watch(
  () => [settingsStore.selectedBrand, settingsStore.period.period_start, settingsStore.period.period_end],
  () => {
    fetchAllData()
  }
)

// Computed properties for objectives
const objectivesInfo = computed(() => {
  if (!representativeData.value) return null
  
  const selectedBrand = settingsStore.selectedBrand
  const objectives = representativeData.value.objectives
  
  // Try selected brand first, then 'ALL'
  if (selectedBrand && objectives[selectedBrand]) {
    return {
      source: 'brand',
      brand: selectedBrand,
      data: objectives[selectedBrand]
    }
  } else if (objectives['ALL']) {
    return {
      source: 'all',
      brand: 'ALL',
      data: objectives['ALL']
    }
  }
  
  return null
})

const hasObjectives = computed(() => {
  return objectivesInfo.value !== null
})

const salesPerCustomerObjective = computed(() => {
  return objectivesInfo.value?.data?.salesPerCustomer || 0
})

const activeCustomersObjective = computed(() => {
  return objectivesInfo.value?.data?.activeCustomers || 0
})

const objectiveBrandContext = computed(() => {
  if (!objectivesInfo.value) return 'No objectives set'
  return objectivesInfo.value.source === 'brand' 
    ? getBrandDisplayName(objectivesInfo.value.brand)
    : 'All Brands'
})

// Computed properties for sales comparison
const hasSalesObjective = computed(() => {
  return salesPerCustomerObjective.value > 0 && statsData.active_customers > 0
})

const salesObjective = computed(() => {
  return salesPerCustomerObjective.value * statsData.active_customers
})

const salesRemaining = computed(() => {
  return Math.max(0, salesObjective.value - statsData.sales)
})

const salesProgressPercentage = computed(() => {
  if (!hasSalesObjective.value) return 0
  return Math.min(100, Math.round((statsData.sales / salesObjective.value) * 100))
})

const salesProgressType = computed(() => {
  if (!hasSalesObjective.value) return 'info'
  if (salesProgressPercentage.value >= 100) return 'success'
  if (salesProgressPercentage.value >= 75) return 'warning'
  return 'danger'
})

const salesRemainingClass = computed(() => {
  return salesRemaining.value > 0 ? 'remaining-positive' : 'remaining-negative'
})

// Computed properties for customers comparison
const hasActiveCustomersObjective = computed(() => {
  return activeCustomersObjective.value > 0
})

const customersRemaining = computed(() => {
  return Math.max(0, activeCustomersObjective.value - statsData.active_customers)
})

const customersProgressPercentage = computed(() => {
  if (!hasActiveCustomersObjective.value) return 0
  return Math.min(100, Math.round((statsData.active_customers / activeCustomersObjective.value) * 100))
})

const customersProgressType = computed(() => {
  if (!hasActiveCustomersObjective.value) return 'info'
  if (customersProgressPercentage.value >= 100) return 'success'
  if (customersProgressPercentage.value >= 75) return 'warning'
  return 'danger'
})

const customersRemainingClass = computed(() => {
  return customersRemaining.value > 0 ? 'remaining-positive' : 'remaining-negative'
})

// Formatted period for display
const formattedPeriod = computed(() => {
  return `${settingsStore.period.period_start} to ${settingsStore.period.period_end}`
})

// Fetch all required data
const fetchAllData = async () => {
  loading.value = true
  fetchError.value = null
  
  try {
    await Promise.all([
      fetchBrands(),
      fetchRepresentativeData(),
      fetchStatisticsData()
    ])
  } catch (error) {
    console.error('Failed to fetch all data:', error)
    fetchError.value = 'Failed to load statistics data. Please try again.'
  } finally {
    loading.value = false
  }
}

// Fetch brands for display names
const fetchBrands = async () => {
  try {
    const response = await api.get('/api/v1/settings/brand')
    brands.value = response.data
  } catch (error) {
    console.error('Failed to fetch brands:', error)
  }
}

// Fetch representative data for objectives
const fetchRepresentativeData = async () => {
  try {
    const response = await api.get('/api/v1/rep/')
    representativeData.value = response.data
  } catch (error) {
    console.error('Failed to fetch representative data:', error)
  }
}

// Fetch statistics data
const fetchStatisticsData = async () => {
  const params: Record<string, string> = {
    start_date: settingsStore.period.period_start,
    end_date: settingsStore.period.period_end
  }
  
  // Only add brand if it's set
  if (settingsStore.selectedBrand) {
    params.brand = settingsStore.selectedBrand
  }
  
  try {
    // Fetch sales data
    const salesResponse = await api.get('/api/v1/statistics/sales', {
      params
    })
    
    // Fetch customers data
    const customersResponse = await api.get('/api/v1/statistics/customers', {
      params
    })
    
    // Update stats data
    Object.assign(statsData, {
      ...salesResponse.data,
      ...customersResponse.data
    })
    
  } catch (error) {
    console.error('Failed to fetch statistics:', error)
    throw error
  }
}

// Helper functions
const getBrandDisplayName = (brandName: string) => {
  const brand = brands.value.find(b => b.brand_name === brandName)
  return brand ? brand.showed_brand_name : brandName
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const calculatePercentage = (part: number, total: number) => {
  if (total === 0) return 0
  return Math.round((part / total) * 100)
}
</script>

<style scoped>
.statistics-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.period-display {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.period-label {
  font-weight: 500;
}

.period-dates {
  font-weight: 600;
  color: #409eff;
}

.filters-card,
.objectives-info-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.filters-content {
  padding: 16px 0;
}

.filter-row {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-weight: 500;
  min-width: 120px;
}

.filter-help {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.data-status {
  margin-top: 16px;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
}

.objectives-content {
  padding: 16px 0;
}

.no-objectives {
  padding: 20px 0;
}

.objectives-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.objective-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.objective-label {
  font-weight: 500;
  color: #303133;
}

.objective-value {
  font-weight: 600;
  font-size: 18px;
  color: #409eff;
}

.objective-context {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  margin-left: 8px;
}

/* Statistics Grid */
.statistics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 24px;
}

@media (max-width: 1200px) {
  .statistics-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-content {
  padding: 24px 0;
}

.stat-main {
  text-align: center;
  margin-bottom: 24px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-label {
  color: #606266;
  font-weight: 500;
}

.detail-value {
  font-weight: 600;
  color: #409eff;
}

/* Sales Channels */
.channel-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.channel-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
  border: 1px solid #ebeef5;
}

.channel-value {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
  color: #303133;
}

.channel-label {
  font-size: 12px;
  color: #909399;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.channel-percentage {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
}

.returns-item .channel-value.negative {
  color: #f56c6c;
}

/* Customer Metrics */
.customer-main {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.customer-group {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.customer-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
  color: #303133;
}

.customer-label {
  font-size: 12px;
  color: #909399;
  text-transform: uppercase;
}

/* Comparison Section */
.stat-comparison {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.comparison-label {
  color: #606266;
  font-weight: 500;
}

.comparison-value {
  font-weight: 600;
}

.remaining-positive {
  color: #f56c6c;
}

.remaining-negative {
  color: #67c23a;
}

.stat-help {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
}

:deep(.el-card__header) {
  padding: 20px 24px;
}

:deep(.el-card__body) {
  padding: 0 24px 24px;
}
</style>