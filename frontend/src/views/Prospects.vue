<template>
  <div class="prospects-container">
    <div class="page-header">
      <h1>Prospects Management</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateForm" icon="Plus">
          Create Prospect
        </el-button>
        <el-button @click="exportToCSV" icon="Download">
          Export CSV
        </el-button>
      </div>
    </div>

    <div class="filters-section">
      <el-input
        v-model="searchQuery"
        placeholder="Search prospects..."
        clearable
        style="width: 300px; margin-right: 15px;"
        @clear="fetchProspects"
        @keyup.enter="fetchProspects"
      >
        <template #suffix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select
        v-model="statusFilter"
        placeholder="Filter by status"
        clearable
        @change="fetchProspects"
        style="width: 200px; margin-right: 15px;"
      >
        <el-option
          v-for="status in statusOptions"
          :key="status"
          :label="status"
          :value="status"
        />
      </el-select>
      
      <el-select
        v-model="favoriteFilter"
        placeholder="Favorites"
        clearable
        @change="fetchProspects"
        style="width: 120px;"
      >
        <el-option label="Favorites" value="true" />
        <el-option label="Non-Favorites" value="false" />
      </el-select>
    </div>

    <el-table
      :data="prospects"
      v-loading="loading"
      style="width: 100%"
      :default-sort="{ prop: 'created_at', order: 'descending' }"
      @sort-change="handleSortChange"
    >
      <el-table-column prop="favorite" width="60" align="center">
        <template #default="{ row }">
          <el-icon 
            :size="20" 
            :color="row.favorite ? '#ffc107' : '#dcdfe6'" 
            class="favorite-icon"
            @click="toggleFavorite(row)"
            style="cursor: pointer;"
          >
            <StarFilled v-if="row.favorite" />
            <Star v-else />
          </el-icon>
        </template>
      </el-table-column>

      <el-table-column prop="name" label="Name" sortable="custom" min-width="150" />
      <el-table-column prop="contact_name" label="Contact" sortable="custom" min-width="150" />
      <el-table-column prop="email" label="Email" sortable="custom" min-width="200" />
      <el-table-column prop="phone" label="Phone" sortable="custom" min-width="130" />
      
      <el-table-column prop="status" label="Status" sortable="custom" width="120">
        <template #default="{ row }">
          <el-tag
            :type="statusTagType(row.status)"
            size="small"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="prospect_interest" label="P. Interest" sortable="custom" width="120" align="center">
        <template #default="{ row }">
          <el-rate
            v-model="row.prospect_interest"
            disabled
            :max="5"
            show-score
            text-color="#ff9900"
            score-template="{value}"
          />
        </template>
      </el-table-column>

      <el-table-column prop="commercial_interest" label="C. Interest" sortable="custom" width="120" align="center">
        <template #default="{ row }">
          <el-rate
            v-model="row.commercial_interest"
            disabled
            :max="5"
            show-score
            text-color="#ff9900"
            score-template="{value}"
          />
        </template>
      </el-table-column>

      <el-table-column prop="overall_interest" label="Overall" sortable="custom" width="100" align="center">
        <template #default="{ row }">
          <span class="overall-interest">
            {{ row.prospect_interest + row.commercial_interest }}/10
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="city" label="City" sortable="custom" width="120" />
      <el-table-column prop="postal_code" label="Postal Code" sortable="custom" width="120" />
      <el-table-column prop="country" label="Country" sortable="custom" width="120" />
      
      <el-table-column prop="brands" label="Brands" min-width="180">
        <template #default="{ row }">
          <div class="brands-display">
            <el-tag
              v-for="brand in row.brands"
              :key="brand"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ getBrandDisplayName(brand) }}
            </el-tag>
            <span v-if="!row.brands || row.brands.length === 0">-</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="next_visit" label="Next Visit" sortable="custom" width="140">
        <template #default="{ row }">
          {{ formatDate(row.next_visit) }}
        </template>
      </el-table-column>

      <el-table-column label="Actions" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDetails(row)" icon="View">
            View
          </el-button>
          <el-dropdown trigger="click">
            <el-button size="small" icon="More" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="editProspect(row)">
                  <el-icon><Edit /></el-icon> Edit
                </el-dropdown-item>
                <el-dropdown-item @click="locateProspect(row)">
                  <el-icon><Location /></el-icon> Locate
                </el-dropdown-item>
                <el-dropdown-item 
                  @click="deleteProspect(row)" 
                  divided 
                  class="danger-item"
                >
                  <el-icon><Delete /></el-icon> Delete
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="totalCount"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="fetchProspects"
      @current-change="fetchProspects"
      style="margin-top: 20px; justify-content: flex-end;"
    />

    <!-- Prospect Detail Dialog -->
    <prospect-detail
      v-model:visible="detailVisible"
      :prospect="selectedProspect"
      :available-brands="availableBrands"
      @update-prospect="editProspect"
    />

    <!-- Prospect Form Dialog -->
    <prospect-form
      v-model:visible="formVisible"
      :prospect="editingProspect"
      :mode="formMode"
      :available-brands="availableBrands"
      @saved="handleProspectSaved"
      @closed="handleFormClosed"
    />
  </div>
</template>

<script setup lang="ts">
import { Delete, Edit, Location, Search, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref, watch } from 'vue'
import ProspectDetail from '../components/ProspectDetail.vue'
import ProspectForm from '../components/ProspectForm.vue'
import { api, useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

interface Brand {
  brand_name: string
  showed_brand_name: string
}

interface Prospect {
  id: string
  name: string
  contact_name: string
  status: string
  notes: string
  phone: string
  email: string
  city: string
  country: string
  postal_code: string
  address: string
  prospect_interest: number
  commercial_interest: number
  last_visit: string | null
  next_visit: string | null
  latitude: number | null
  longitude: number | null
  brands: string[]
  favorite: boolean
  representative_id: string
  created_at: string
  updated_at: string
}

const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const prospects = ref<Prospect[]>([])
const availableBrands = ref<Brand[]>([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const brandFilter = ref('')
const favoriteFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const sortField = ref('created_at')
const sortOrder = ref('descending')

const detailVisible = ref(false)
const formVisible = ref(false)
const selectedProspect = ref<Prospect | null>(null)
const editingProspect = ref<Prospect | null>(null)
const formMode = ref<'create' | 'edit'>('create')

const statusOptions = ['New', 'Pending', 'Lost', 'Converted', 'Ready', 'Blocked']

const statusTagType = (status: string) => {
  const types: { [key: string]: string } = {
    'New': 'info',
    'Pending': 'warning',
    'Lost': 'danger',
    'Converted': 'success',
    'Ready': 'success',
    'Blocked': 'danger'
  }
  return types[status] || 'info'
}

const getBrandDisplayName = (brandName: string): string => {
  const brand = availableBrands.value.find(b => b.brand_name === brandName)
  return brand ? brand.showed_brand_name : brandName
}

const fetchAvailableBrands = async () => {
  try {
    const response = await api.get('http://localhost:8000/api/v1/settings/brand', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    availableBrands.value = response.data
  } catch (error) {
    console.error('Failed to fetch brands:', error)
    ElMessage.error('Failed to load available brands')
  }
}

watch([searchQuery, statusFilter, brandFilter, favoriteFilter], () => {
  currentPage.value = 1
  fetchProspects()
})

const fetchProspects = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    
    // Add brand filter if selected
    if (settingsStore.selectedBrand) {
      params.append('brand', settingsStore.selectedBrand)
    }
    
    // Add search filter
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    
    // Add status filter
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }
    
    // Add brand filter
    if (brandFilter.value) {
      params.append('brands', brandFilter.value)
    }
    
    // Add favorite filter
    if (favoriteFilter.value !== '') {
      params.append('favorite', favoriteFilter.value)
    }
    
    // Add sorting
    const sortSymbol = sortOrder.value === 'descending' ? 'desc' : 'asc'
    params.append('sort_by', sortField.value)
    params.append('sort_order', sortSymbol)
    
    // Add pagination
    params.append('page', currentPage.value.toString())
    params.append('limit', pageSize.value.toString())
    
    const url = `http://localhost:8000/api/v1/prospect/?${params.toString()}`
    
    const response = await api.get(url, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    
    if (Array.isArray(response.data)) {
      prospects.value = response.data
      totalCount.value = response.data.length
    } else {
      prospects.value = response.data.items
      totalCount.value = response.data.total_count
    }
  } catch (error) {
    console.error('Failed to fetch prospects:', error)
    ElMessage.error('Failed to load prospects')
  } finally {
    loading.value = false
  }
}

const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (prop && order) {
    sortField.value = prop
    sortOrder.value = order
    fetchProspects()
  }
}

const showDetails = (prospect: Prospect) => {
  selectedProspect.value = prospect
  detailVisible.value = true
}

const showCreateForm = () => {
  editingProspect.value = null
  formMode.value = 'create'
  formVisible.value = true
}

const editProspect = (prospect: Prospect) => {
  editingProspect.value = { ...prospect }
  formMode.value = 'edit'
  formVisible.value = true
  detailVisible.value = false
}

const toggleFavorite = async (prospect: Prospect) => {
  try {
    const updatedProspect = { ...prospect, favorite: !prospect.favorite }
    await api.put(
      `http://localhost:8000/api/v1/prospect/${prospect.id}`,
      updatedProspect,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    prospect.favorite = !prospect.favorite
    ElMessage.success(prospect.favorite ? 'Added to favorites' : 'Removed from favorites')
  } catch (error) {
    console.error('Failed to update favorite status:', error)
    ElMessage.error('Failed to update favorite status')
  }
}

const deleteProspect = async (prospect: Prospect) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete prospect "${prospect.name}"? This action cannot be undone.`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await api.delete(
      `http://localhost:8000/api/v1/prospect/${prospect.id}`,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      }
    )
    
    ElMessage.success('Prospect deleted successfully')
    fetchProspects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete prospect:', error)
      ElMessage.error('Failed to delete prospect')
    }
  }
}

const locateProspect = (prospect: Prospect) => {
  if (prospect.latitude && prospect.longitude) {
    window.open(`https://www.google.com/maps?q=${prospect.latitude},${prospect.longitude}`, '_blank')
  } else {
    ElMessage.warning('No location data available for this prospect')
  }
}

const exportToCSV = async () => {
  try {
    const response = await api.get(
      'http://localhost:8000/api/v1/prospect/export/csv',
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        },
        responseType: 'blob'
      }
    )
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'prospects.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    ElMessage.success('CSV export started successfully')
  } catch (error) {
    console.error('Failed to export CSV:', error)
    ElMessage.error('Failed to export prospects to CSV')
  }
}

const handleProspectSaved = () => {
  formVisible.value = false
  fetchProspects()
  ElMessage.success(
    formMode.value === 'create' 
      ? 'Prospect created successfully' 
      : 'Prospect updated successfully'
  )
}

const handleFormClosed = () => {
  formVisible.value = false
  editingProspect.value = null
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  fetchAvailableBrands()
  fetchProspects()
})
</script>

<style scoped>
.prospects-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters-section {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
}

.favorite-icon {
  transition: color 0.2s ease;
}

.favorite-icon:hover {
  color: #ffc107 !important;
}

.overall-interest {
  font-weight: bold;
  color: #409EFF;
}

.danger-item {
  color: #f56c6c;
}

.brands-display {
  display: flex;
  flex-wrap: wrap;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-rate) {
  display: inline-flex;
}
</style>