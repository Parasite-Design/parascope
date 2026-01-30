<template>
  <el-dialog
    v-model="visible"
    :title="customer?.name || 'Customer Details'"
    width="90%"
    :fullscreen="true"
    destroy-on-close
  >
    <div v-if="customer" class="customer-detail">
      <el-row :gutter="20">
        <!-- Left Column - Basic Info -->
        <el-col :span="8">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>Basic Information</span>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Code">
                {{ customer.code }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Department">
                {{ getDepartmentFromCode(customer.code) }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Name">
                {{ customer.name }}
              </el-descriptions-item>
              
              <el-descriptions-item label="City">
                {{ customer.city }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Phone">
                <a :href="`tel:${customer.phone}`" class="phone-link">{{ customer.phone }}</a>
              </el-descriptions-item>
              
              <el-descriptions-item label="Status">
                <el-tag :type="customer.active ? 'success' : 'danger'">
                  {{ customer.active ? 'Active' : 'Inactive' }}
                </el-tag>
              </el-descriptions-item>
              
              <el-descriptions-item label="Favorite">
                <el-icon 
                  :color="customer.favorite ? '#ffc107' : '#dcdfe6'" 
                  class="favorite-icon"
                  style="cursor: pointer;"
                  @click="toggleFavorite"
                >
                  <StarFilled v-if="customer.favorite" />
                  <Star v-else />
                </el-icon>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Sales Summary Card -->
          <el-card class="sales-card" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span>Sales Summary</span>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Current Period Total">
                <span :class="{'highlight-text': customer.period1_total > customer.period2_total}">
                  {{ formatCurrency(customer.period1_total) }}
                </span>
              </el-descriptions-item>
              
              <el-descriptions-item label="Units Sold">
                {{ customer.period1_count }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Last Year Total">
                {{ formatCurrency(customer.period2_total) }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Objective">
                {{ formatCurrency(customer.objective) }}
              </el-descriptions-item>
              
              <el-descriptions-item label="Objective Progress">
                <el-progress 
                  :percentage="calculateProgress(customer.period1_total, customer.objective)" 
                  :status="getProgressStatus(customer.period1_total, customer.objective)"
                  :show-text="true"
                />
              </el-descriptions-item>
              
              <el-descriptions-item label="Total Visits">
                <el-tag :type="customer.visits_count > 0 ? 'success' : 'info'">
                  {{ customer.visits_count }}
                </el-tag>
              </el-descriptions-item>
              
              <el-descriptions-item label="Last Visit">
                {{ formatDate(customer.last_visit) }}
              </el-descriptions-item>

              <el-descriptions-item label="Next Visit">
              <el-tag :type="getNextVisitStatus(customer.next_visit)" v-if="customer.next_visit">
                {{ formatDate(customer.next_visit) }}
              </el-tag>
              <span v-else>-</span>
            </el-descriptions-item>

            <el-descriptions-item label="Priority Score">
              <el-tag :type="getScoreStatus(customer.score)" v-if="customer.score !== undefined">
                {{ customer.score }}
              </el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- Right Column - Map and Charts -->
        <el-col :span="16">
          <!-- Map Card -->
          <el-card class="map-card">
            <template #header>
              <div class="card-header">
                <span>Location</span>
                <el-button 
                  type="primary" 
                  text 
                  @click="openInMaps"
                  v-if="hasCoordinates"
                  :icon="MapLocation"
                >
                  Open in External Maps
                </el-button>
              </div>
            </template>
            <div class="map-container">
              <div v-if="hasCoordinates" class="map-wrapper">
                <iframe
                  :src="mapUrl"
                  width="100%"
                  height="100%"
                  style="border:0;"
                  loading="lazy"
                  referrerpolicy="no-referrer-when-downgrade"
                ></iframe>
              </div>
              <div v-else class="map-placeholder">
                <el-empty description="No location data available" :image-size="100">
                  <el-button type="primary" @click="editCustomer">Add Location</el-button>
                </el-empty>
              </div>
            </div>
          </el-card>

          <!-- Notes Card -->
          <el-card class="notes-card" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span>Notes</span>
                <el-button type="primary" text @click="editNotes" :icon="Edit">
                  {{ customer.note ? 'Edit' : 'Add' }} Notes
                </el-button>
              </div>
            </template>
            <div class="notes-content" :class="{ 'empty-notes': !customer.note }">
              {{ customer.note || 'No notes available. Click "Add Notes" to add some.' }}
            </div>
          </el-card>

          <!-- Sales Chart Card -->
          <el-card class="chart-card" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span>Sales Over Time</span>
                <div class="chart-controls">
                  <el-select 
                    v-model="chartPeriod" 
                    size="small" 
                    style="width: 120px;"
                    @change="fetchCustomerDetails"
                  >
                    <el-option label="3 Months" value="3" />
                    <el-option label="6 Months" value="6" />
                    <el-option label="12 Months" value="12" />
                  </el-select>
                </div>
              </div>
            </template>
            <div class="chart-container">
              <sales-chart 
                v-if="detailedCustomer && detailedCustomer.period_sums?.length" 
                :period-sums="detailedCustomer.period_sums" 
                :loading="detailLoading"
              />
              <div v-else class="no-data-placeholder">
                <el-empty description="No sales data available" :image-size="80" />
              </div>
            </div>
          </el-card>

          <!-- Visits History Card -->
          <el-card class="visits-card" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span>Visit History</span>
                <el-button type="primary" text :icon="Plus" @click="logVisit">
                  Log Visit
                </el-button>
              </div>
            </template>
            <div class="visits-content">
              <el-table 
                v-if="detailedCustomer && hasVisits" 
                :data="processedVisits" 
                v-loading="detailLoading"
                empty-text="No visit history available"
                style="width: 100%"
              >
                <el-table-column prop="date" label="Date" width="150">
                  <template #default="{ row }">
                    {{ formatDate(row.date) }}
                  </template>
                </el-table-column>
                <el-table-column prop="type" label="Type" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getVisitTypeTag(row.type)" size="small">
                      {{ formatVisitType(row.type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="notes" label="Notes" min-width="200" show-overflow-tooltip />
                <el-table-column label="Actions" width="80">
                  <template #default="{ row }">
                    <el-button type="primary" text :icon="View" @click="viewVisitDetails(row)" />
                  </template>
                </el-table-column>
              </el-table>
              <div v-else class="no-data-placeholder">
                <el-empty description="No visit history available" :image-size="80" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Loading state when customer data is being fetched -->
    <div v-else class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <template #footer>
      <el-button @click="visible = false">Close</el-button>
      <el-button type="primary" @click="editCustomer" :icon="Edit">
        Edit Customer
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { Edit, MapLocation, Plus, Star, StarFilled, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, ref, watch } from 'vue'
import { api, useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import SalesChart from './SalesChart.vue'

interface Customer {
  _id: string
  code: string
  city: string
  latitude: string
  longitude: string
  name: string
  phone: string
  score: number
  period1_total: number
  period1_count: number
  period2_total: number
  objective: number
  visits_count: number
  favorite: boolean
  active: boolean
  period_progress: number
  objective_progress: number
  last_visit: string | null
  next_visit: string | null
  note?: string,
}

interface Visit {
  date: string
  type?: string
  notes?: string
  [key: string]: any
}

interface DetailedCustomer extends Customer {
  visits: Visit[]
  period_sums: Array<{
    start: string
    end: string
    total: number
    count: number
  }>
}

// Add these methods to your CustomerDetail.vue script

const getNextVisitStatus = (nextVisit: string | null) => {
  if (!nextVisit) return 'info'
  
  const now = new Date()
  const visitDate = new Date(nextVisit)
  const daysUntilVisit = Math.ceil((visitDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  
  if (daysUntilVisit < 0) return 'danger' // Overdue
  if (daysUntilVisit <= 7) return 'warning' // Within a week
  if (daysUntilVisit <= 30) return 'primary' // Within a month
  return 'success' // More than a month away
}

const getScoreStatus = (score: number | undefined) => {
  if (score === undefined) return 'info'
  if (score >= 10000) return 'danger' // Very high priority
  if (score >= 5000) return 'warning' // High priority
  if (score >= 1000) return 'primary' // Medium priority
  return 'success' // Low priority
}

const props = defineProps<{
  visible: boolean
  customer: Customer | null
}>()

const emit = defineEmits(['update:visible', 'refresh-data', 'edit-customer'])

const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const visible = ref(props.visible)
const detailedCustomer = ref<DetailedCustomer | null>(null)
const detailLoading = ref(false)
const chartPeriod = ref('6') // Default to 6 months

// Computed properties
const hasCoordinates = computed(() => {
  return props.customer?.latitude && props.customer?.longitude && 
         props.customer.latitude !== '' && props.customer.longitude !== '' &&
         !isNaN(parseFloat(props.customer.latitude)) && !isNaN(parseFloat(props.customer.longitude))
})

const mapUrl = computed(() => {
  if (!props.customer?.latitude || !props.customer?.longitude) return ''
  const lat = parseFloat(props.customer.latitude)
  const lng = parseFloat(props.customer.longitude)
  return `https://maps.google.com/maps?q=${lat},${lng}&z=15&output=embed`
})

const hasVisits = computed(() => {
  return detailedCustomer.value?.visits && detailedCustomer.value.visits.length > 0
})

const processedVisits = computed(() => {
  if (!detailedCustomer.value?.visits) return []
  
  return detailedCustomer.value.visits.map(visit => ({
    ...visit,
    // Ensure type has a default value if undefined
    type: visit.type || 'unknown',
    // Ensure notes has a default value if undefined
    notes: visit.notes || 'No notes'
  }))
})

// Watchers
watch(() => props.visible, async (val) => {
  visible.value = val
  if (val && props.customer) {
    await fetchCustomerDetails()
  } else {
    detailedCustomer.value = null
  }
})

watch(() => props.customer, async (val) => {
  if (val && visible.value) {
    await fetchCustomerDetails()
  }
})

watch(visible, (val) => {
  emit('update:visible', val)
  if (!val) {
    detailedCustomer.value = null
  }
})

// Methods
const fetchCustomerDetails = async () => {
  if (!props.customer) return
  
  detailLoading.value = true
  try {
    const periodStart = settingsStore.period.period_start
    const periodEnd = settingsStore.period.period_end
    
    const response = await api.get(
      `http://localhost:8000/api/v1/customers/${props.customer._id}?month_interval=${chartPeriod.value}&period_start=${periodStart}&period_end=${periodEnd}`,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      }
    )
    
    detailedCustomer.value = response.data
  } catch (error) {
    console.error('Failed to fetch customer details:', error)
    ElMessage.error('Failed to load customer details')
    // Initialize with basic customer data
    if (props.customer) {
      detailedCustomer.value = {
        ...props.customer,
        visits: [],
        period_sums: []
      }
    }
  } finally {
    detailLoading.value = false
  }
}

const getDepartmentFromCode = (code: string) => {
  return code.substring(0, 2)
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('fr-CH', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-CH')
}

const calculateProgress = (current: number, objective: number) => {
  if (!objective || objective === 0) return 0
  return Math.min(Math.round((current / objective) * 100), 100)
}

const getProgressStatus = (current: number, objective: number) => {
  const progress = calculateProgress(current, objective)
  if (progress >= 100) return 'success'
  if (progress >= 70) return 'warning'
  return 'exception'
}

const getVisitTypeTag = (type: string | undefined) => {
  // Handle undefined or null types
  if (!type) return 'default'
  
  const typeMap: Record<string, string> = {
    'visit': 'primary',
    'call': 'success',
    'email': 'info',
    'meeting': 'warning',
    'other': 'default',
    'unknown': 'info'
  }
  
  const normalizedType = type.toLowerCase().trim()
  return typeMap[normalizedType] || 'default'
}

const formatVisitType = (type: string | undefined) => {
  if (!type) return 'Unknown'
  
  // Capitalize first letter of each word
  return type.split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

const openInMaps = () => {
  if (props.customer?.latitude && props.customer?.longitude) {
    window.open(
      `https://www.google.com/maps?q=${props.customer.latitude},${props.customer.longitude}`,
      '_blank'
    )
  }
}

const editCustomer = () => {
  if (props.customer) {
    emit('edit-customer', props.customer)
    visible.value = false
  }
}

const editNotes = async () => {
  if (!props.customer) return
  
  try {
    const { value } = await ElMessageBox.prompt('Edit customer notes:', 'Notes', {
      confirmButtonText: 'Save',
      cancelButtonText: 'Cancel',
      inputType: 'textarea',
      inputValue: props.customer?.note || '',
      inputPlaceholder: 'Enter notes about this customer...',
      roundButton: true,
      inputValidator: (value: string) => {
        if (value && value.length > 1000) {
          return 'Notes cannot exceed 1000 characters'
        }
        return true
      }
    })
    
    // Update notes via API
    const updatedCustomer = { note: value }
    await api.put(
      `http://localhost:8000/api/v1/customers/${props.customer._id}`,
      updatedCustomer,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    // Update local state
    if (props.customer) {
      props.customer.note = value
    }
    if (detailedCustomer.value) {
      detailedCustomer.value.note = value
    }
    
    ElMessage.success('Notes updated successfully')
    emit('refresh-data') // Notify parent to refresh data
  } catch (error: any) {
    // User cancelled or validation failed
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('Failed to update notes')
    }
  }
}

const toggleFavorite = async () => {
  if (!props.customer) return
  
  try {
    const updatedCustomer = { favorite: !props.customer.favorite }
    await api.put(
      `http://localhost:8000/api/v1/customers/${props.customer._id}`,
      updatedCustomer,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    // Update local state
    if (props.customer) {
      props.customer.favorite = !props.customer.favorite
    }
    if (detailedCustomer.value) {
      detailedCustomer.value.favorite = !detailedCustomer.value.favorite
    }
    
    ElMessage.success(props.customer.favorite ? 'Added to favorites' : 'Removed from favorites')
    emit('refresh-data') // Notify parent to refresh data
  } catch (error) {
    console.error('Failed to update favorite status:', error)
    ElMessage.error('Failed to update favorite status')
  }
}

const logVisit = () => {
  ElMessage.info('Visit logging feature to be implemented')
}

const viewVisitDetails = (visit: Visit) => {
  ElMessageBox.alert(visit.notes || 'No details available', `Visit on ${formatDate(visit.date)}`, {
    confirmButtonText: 'Close',
    roundButton: true
  })
}
</script>

<style scoped>
.customer-detail {
  max-height: 80vh;
  overflow-y: auto;
  padding: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.map-container {
  height: 300px;
  background-color: #f8f9fa;
  border-radius: 4px;
  overflow: hidden;
}

.map-wrapper {
  height: 100%;
  width: 100%;
}

.map-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.notes-content {
  white-space: pre-wrap;
  line-height: 1.5;
  min-height: 60px;
  padding: 8px 0;
}

.notes-content.empty-notes {
  color: #909399;
  font-style: italic;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visits-content {
  max-height: 400px;
  overflow-y: auto;
}

.loading-placeholder {
  padding: 20px;
}

.loading-container {
  padding: 20px;
}

.no-data-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.phone-link {
  color: #409eff;
  text-decoration: none;
}

.phone-link:hover {
  text-decoration: underline;
}

.favorite-icon {
  transition: color 0.2s ease;
}

.favorite-icon:hover {
  transform: scale(1.1);
}

.highlight-text {
  color: #67c23a;
  font-weight: 600;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Responsive design */
@media (max-width: 768px) {
  .el-col {
    width: 100%;
  }
  
  .customer-detail {
    max-height: none;
    overflow-y: visible;
  }
}
</style>