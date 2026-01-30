<template>
  <div class="customers-container">
    <div class="page-header">
      <h1>Customers Management</h1>
    </div>

    <div class="filters-section">
      <el-input
        v-model="departmentSearch"
        placeholder="Search by department (first 2 digits of code)"
        clearable
        style="width: 300px; margin-right: 15px;"
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
        style="width: 120px; margin-right: 15px;"
      >
        <el-option label="Favorites" value="true" />
        <el-option label="Non-Favorites" value="false" />
      </el-select>

      <el-select
        v-model="activeFilter"
        placeholder="Active"
        clearable
        @change="applyFilters"
        style="width: 120px;"
      >
        <el-option label="Active" value="true" />
        <el-option label="Inactive" value="false" />
      </el-select>
    </div>

    <el-table
      :data="customers"
      v-loading="loading"
      style="width: 100%"
      @row-click="showCustomerDetails"
      @sort-change="handleSortChange"
      class="customers-table"
    >
      <el-table-column prop="favorite" width="60" align="center" sortable="custom">
        <template #default="{ row }">
          <el-icon 
            :size="20" 
            :color="row.favorite ? '#ffc107' : '#dcdfe6'" 
            class="favorite-icon"
            @click.stop="toggleFavorite(row)"
            style="cursor: pointer;"
          >
            <StarFilled v-if="row.favorite" />
            <Star v-else />
          </el-icon>
        </template>
      </el-table-column>

      <el-table-column prop="code" label="Code" sortable="custom" width="120" />
      
      <el-table-column prop="department" label="Department" sortable="custom" width="120">
        <template #default="{ row }">
          {{ getDepartmentFromCode(row.code) }}
        </template>
      </el-table-column>

      <el-table-column prop="name" label="Name" sortable="custom" min-width="200" />
      <el-table-column prop="city" label="City" sortable="custom" width="150" />
      <el-table-column prop="phone" label="Phone" sortable="custom" width="150" />
      
      <el-table-column prop="active" label="Status" sortable="custom" width="100">
        <template #default="{ row }">
          <el-tag :type="row.active ? 'success' : 'danger'" size="small">
            {{ row.active ? 'Active' : 'Inactive' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- New Priority Score Column -->
      <el-table-column prop="score" label="Priority" sortable="custom" width="100" align="center">
        <template #default="{ row }">
          <el-tag 
            v-if="row.score !== undefined && row.score !== null" 
            :type="getScoreStatus(row.score)" 
            size="small"
            style="cursor: help;"
            :title="getScoreTooltip(row.score)"
          >
            {{ formatScore(row.score) }}
          </el-tag>
          <el-tag v-else type="info" size="small">-</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="period1_total" label="Total" sortable="custom" width="120" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.period1_total) }}
        </template>
      </el-table-column>

      <el-table-column prop="period1_count" label="Units" sortable="custom" width="100" align="center">
        <template #default="{ row }">
          {{ row.period1_count }}
        </template>
      </el-table-column>

      <el-table-column prop="period2_total" label="Last Year Total" sortable="custom" width="150" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.period2_total) }}
        </template>
      </el-table-column>

      <el-table-column prop="objective" label="Objective" sortable="custom" width="120" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.objective) }}
        </template>
      </el-table-column>

      <el-table-column prop="objective_progress" label="Objective Progress" sortable="custom" width="140" align="center">
        <template #default="{ row }">
          <el-progress 
            :percentage="calculateProgress(row.period1_total, row.objective)" 
            :status="getProgressStatus(row.period1_total, row.objective)"
            style="width: 100px;"
          />
        </template>
      </el-table-column>

      <el-table-column prop="visits_count" label="Visits" sortable="custom" width="80" align="center" />
      
      <el-table-column prop="last_visit" label="Last Visit" sortable="custom" width="120">
        <template #default="{ row }">
          {{ formatDate(row.last_visit) }}
        </template>
      </el-table-column>

      <!-- New Next Visit Column -->
      <el-table-column prop="next_visit" label="Next Visit" sortable="custom" width="120">
        <template #default="{ row }">
          <el-tag 
            v-if="row.next_visit" 
            :type="getNextVisitStatus(row.next_visit)" 
            size="small"
            style="cursor: help;"
            :title="getNextVisitTooltip(row.next_visit)"
          >
            {{ formatDate(row.next_visit) }}
          </el-tag>
          <el-tag v-else type="info" size="small">Not scheduled</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="Actions" width="100" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="editCustomer(row)" icon="Edit">
            Edit
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="totalCount"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handlePaginationChange"
      @current-change="handlePaginationChange"
      style="margin-top: 20px; justify-content: flex-end;"
    />

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
import { Search, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref, watch } from 'vue'
import CustomerDetail from '../components/CustomerDetail.vue'
import CustomerEdit from '../components/CustomerEdit.vue'
import { api, useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

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

interface SortParams {
  prop: string
  order: 'ascending' | 'descending' | null
}

const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const customers = ref<Customer[]>([])
const loading = ref(false)
const departmentSearch = ref('')
const favoriteFilter = ref('')
const activeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const sortParams = ref<SortParams>({ prop: '', order: null })

const detailVisible = ref(false)
const editVisible = ref(false)
const selectedCustomer = ref<Customer | null>(null)
const editingCustomer = ref<Customer | null>(null)

const allCustomers = ref<Customer[]>([])
const filteredCustomers = ref<Customer[]>([])

// Add these methods to your component
const getNextVisitStatus = (nextVisit: string | null) => {
  if (!nextVisit) return 'info'
  
  const now = new Date()
  const visitDate = new Date(nextVisit)
  
  // Handle invalid dates
  if (isNaN(visitDate.getTime())) return 'info'
  
  const daysUntilVisit = Math.ceil((visitDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  
  if (daysUntilVisit < 0) return 'danger' // Overdue
  if (daysUntilVisit <= 7) return 'warning' // Within a week
  if (daysUntilVisit <= 30) return 'primary' // Within a month
  return 'success' // More than a month away
}

const getNextVisitTooltip = (nextVisit: string | null) => {
  if (!nextVisit) return 'Next visit not scheduled'
  
  const now = new Date()
  const visitDate = new Date(nextVisit)
  
  if (isNaN(visitDate.getTime())) return 'Invalid date'
  
  const daysUntilVisit = Math.ceil((visitDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  
  if (daysUntilVisit < 0) return `Overdue by ${Math.abs(daysUntilVisit)} days`
  if (daysUntilVisit === 0) return 'Due today'
  if (daysUntilVisit === 1) return 'Due tomorrow'
  return `Due in ${daysUntilVisit} days`
}

const getScoreStatus = (score: number | undefined | null) => {
  if (score === undefined || score === null) return 'info'
  if (score >= 10000) return 'danger' // Very high priority
  if (score >= 5000) return 'warning' // High priority
  if (score >= 1000) return 'primary' // Medium priority
  return 'success' // Low priority
}

const getScoreTooltip = (score: number | undefined | null) => {
  if (score === undefined || score === null) return 'Priority score not calculated'
  
  if (score >= 10000) return 'Very high priority - Contact immediately'
  if (score >= 5000) return 'High priority - Contact soon'
  if (score >= 1000) return 'Medium priority - Schedule contact'
  return 'Low priority - Contact when available'
}

const formatScore = (score: number) => {
  if (score >= 1000) {
    return `${(score / 1000).toFixed(1)}k`
  }
  return Math.round(score).toString()
}

const getDepartmentFromCode = (code: string) => {
  return code.substring(0, 2)
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

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('fr-CH', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const fetchCustomers = async () => {
  loading.value = true
  try {
    const period1Start = settingsStore.period.period_start
    const period1End = settingsStore.period.period_end

    const period1StartDate = new Date(period1Start)
    const period1EndDate = new Date(period1End)

    const period2Start = new Date(period1StartDate.getFullYear() - 1, period1StartDate.getMonth(), period1StartDate.getDate()).toISOString().split('T')[0]
    const period2End = new Date(period1EndDate.getFullYear() - 1, period1EndDate.getMonth(), period1EndDate.getDate()).toISOString().split('T')[0]
  

    const url = `http://localhost:8000/api/v1/customers/?period1_start=${period1Start}&period1_end=${period1End}&period2_start=${period2Start}&period2_end=${period2End}`

    const response = await api.get(url, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    
    allCustomers.value = response.data
    applyFilters()
    
  } catch (error) {
    console.error('Failed to fetch customers:', error)
    ElMessage.error('Failed to load customers')
  } finally {
    loading.value = false
  }
}

const handleSortChange = (params: SortParams) => {
  sortParams.value = params
  applyFilters()
}

const sortData = (data: Customer[]) => {
  if (!sortParams.value.prop || !sortParams.value.order) {
    return data
  }

  const { prop, order } = sortParams.value
  
  return [...data].sort((a, b) => {
    let aValue: any = a[prop as keyof Customer]
    let bValue: any = b[prop as keyof Customer]

    // Handle computed fields
    if (prop === 'department') {
      aValue = getDepartmentFromCode(a.code)
      bValue = getDepartmentFromCode(b.code)
    } else if (prop === 'objective_progress') {
      aValue = calculateProgress(a.period1_total, a.objective)
      bValue = calculateProgress(b.period1_total, b.objective)
    }

    // Handle null/undefined values
    if (aValue == null) aValue = ''
    if (bValue == null) bValue = ''

    // Handle different data types
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (aValue < bValue) {
      return order === 'ascending' ? -1 : 1
    }
    if (aValue > bValue) {
      return order === 'ascending' ? 1 : -1
    }
    return 0
  })
}

const applyFilters = () => {
  let result = [...allCustomers.value]
  
  // Apply department filter
  if (departmentSearch.value) {
    result = result.filter(customer => 
      customer.code.substring(0, 2) === departmentSearch.value
    )
  }
  
  // Apply favorite filter
  if (favoriteFilter.value !== '') {
    const fav = favoriteFilter.value === 'true'
    result = result.filter(customer => customer.favorite === fav)
  }
  
  // Apply active filter
  if (activeFilter.value !== '') {
    const active = activeFilter.value === 'true'
    result = result.filter(customer => customer.active === active)
  }
  
  // Apply sorting
  result = sortData(result)
  
  filteredCustomers.value = result
  totalCount.value = result.length
  
  // Apply pagination
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  customers.value = result.slice(start, end)
}

watch([departmentSearch, favoriteFilter, activeFilter], () => {
  currentPage.value = 1
  applyFilters()
})

const handlePaginationChange = () => {
  applyFilters()
}

const showCustomerDetails = (customer: Customer) => {
  selectedCustomer.value = customer
  detailVisible.value = true
}

const editCustomer = (customer: Customer) => {
  editingCustomer.value = { ...customer }
  editVisible.value = true
}

const toggleFavorite = async (customer: Customer) => {
  try {
    const updatedCustomer = { favorite: !customer.favorite }
    await api.put(
      `http://localhost:8000/api/v1/customers/${customer._id}`,
      updatedCustomer,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    customer.favorite = !customer.favorite
    ElMessage.success(customer.favorite ? 'Added to favorites' : 'Removed from favorites')
  } catch (error) {
    console.error('Failed to update favorite status:', error)
    ElMessage.error('Failed to update favorite status')
  }
}

onMounted(() => {
  fetchCustomers()
})
</script>

<style scoped>
.customers-container {
  padding: 20px;
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
}

.customers-table {
  margin-top: 20px;
}

.customers-table :deep(.el-table__row) {
  cursor: pointer;
}

.customers-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.favorite-icon {
  transition: color 0.2s ease;
}

.favorite-icon:hover {
  color: #ffc107 !important;
}
</style>