<template>
  <div class="objectives-container">
    <div class="page-header">
      <h1>Objectives Management</h1>
    </div>

    <!-- Table View of All Representatives and Their Objectives -->
    <el-card class="objectives-table-card">
      <template #header>
        <div class="card-header">
          <span>All Representatives & Objectives</span>
          <div class="header-actions">
            <el-button @click="refreshData" :loading="loading" icon="Refresh" size="small">
              Refresh
            </el-button>
          </div>
        </div>
      </template>

      <!-- Representatives Table -->
      <div class="table-container">
        <el-table 
          :data="representatives" 
          v-loading="loading"
          :row-key="(row: { id: any }) => row.id"
          style="width: 100%;"
        >
          <el-table-column prop="code" label="Code" width="80" sortable />
          <el-table-column prop="key" label="Key" width="120" />
          <el-table-column prop="name" label="Name" min-width="180" />
          
          <!-- Objectives Column -->
          <el-table-column label="Objectives" min-width="350">
            <template #default="{ row }">
              <div class="objectives-list">
                <div v-if="Object.keys(row.objectives).length === 0" class="no-objectives">
                  <el-tag type="info" size="small">No objectives set</el-tag>
                </div>
                <div v-else class="objectives-items">
                  <div 
                    v-for="(brandObj, brandName) in row.objectives" 
                    :key="brandName"
                    class="objective-item"
                  >
                    <div class="objective-header">
                      <strong>{{ getBrandDisplayName(brandName) }}</strong>
                    </div>
                    <div class="objective-details">
                      <div v-if="brandObj.salesPerCustomer" class="objective-detail">
                        <span class="type-label">Sales per Customer:</span>
                        <span class="type-value">{{ formatValue(brandObj.salesPerCustomer, 'salesPerCustomer') }}</span>
                      </div>
                      <div v-if="brandObj.activeCustomers" class="objective-detail">
                        <span class="type-label">Active Customers:</span>
                        <span class="type-value">{{ formatValue(brandObj.activeCustomers, 'activeCustomers') }}</span>
                      </div>
                      <div v-if="!brandObj.salesPerCustomer && !brandObj.activeCustomers" class="no-objective-details">
                        <el-tag type="info" size="small">No objectives set for this brand</el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="Actions" width="150" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                @click="showSetObjectiveDialog(row)" 
                size="small"
                icon="Plus"
              >
                Add Objective
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- Dialog for Setting/Editing Objectives -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="objectiveFormRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        :disabled="submitting"
      >
        <el-form-item label="Representative" prop="rep_id">
          <el-select
            v-model="formData.rep_id"
            placeholder="Select representative"
            filterable
            style="width: 100%;"
            :disabled="selectedRepId !== null"
          >
            <el-option
              v-for="rep in representatives"
              :key="rep.id"
              :label="`${rep.key} - ${rep.name || 'No name'}`"
              :value="rep.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Brand" prop="brand_name">
          <el-select
            v-model="formData.brand_name"
            placeholder="Select brand"
            filterable
            style="width: 100%;"
            :disabled="editingMode"
          >
            <el-option
              label="All Brands"
              value="ALL"
            />
            <el-option
              v-for="brand in availableBrands"
              :key="brand.brand_name"
              :label="brand.showed_brand_name"
              :value="brand.brand_name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Objective Type" prop="type">
          <el-select
            v-model="formData.type"
            placeholder="Select objective type"
            style="width: 100%;"
            :disabled="editingMode"
          >
            <el-option label="Sales Per Customer" value="salesPerCustomer" />
            <el-option label="Active Customers" value="activeCustomers" />
          </el-select>
        </el-form-item>

        <el-form-item 
          :label="getValueLabel()" 
          prop="value"
        >
          <el-input-number
            v-model="formData.value"
            :placeholder="getValuePlaceholder()"
            :min="0"
            :step="formData.type === 'salesPerCustomer' ? 100 : 1"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose" :disabled="submitting">
            Cancel
          </el-button>
          <el-button 
            type="primary" 
            @click="submitForm" 
            :loading="submitting"
          >
            {{ isEditing ? 'Update' : 'Set' }} Objective
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

interface Representative {
  id: string
  code: number
  key: string
  name: string
  objectives: Record<string, {
    salesPerCustomer?: number
    activeCustomers?: number
  }>
}

interface Brand {
  brand_name: string
  showed_brand_name: string
}

interface ObjectiveForm {
  rep_id: string
  brand_name: string
  type: 'salesPerCustomer' | 'activeCustomers'
  value: number
}

const authStore = useAuthStore()

const representatives = ref<Representative[]>([])
const brands = ref<Brand[]>([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const selectedRepId = ref<string | null>(null)
const editingMode = ref(false)
const isEditing = ref(false)

// Store editing context for validation
const editingContext = ref<{
  brand_name: string
  type: 'salesPerCustomer' | 'activeCustomers'
} | null>(null)

const objectiveFormRef = ref<FormInstance>()
const formData = reactive<ObjectiveForm>({
  rep_id: '',
  brand_name: '',
  type: 'salesPerCustomer',
  value: 0
})

const formRules: FormRules = {
  rep_id: [
    { required: true, message: 'Please select a representative', trigger: 'change' }
  ],
  brand_name: [
    { required: true, message: 'Please select a brand', trigger: 'change' }
  ],
  type: [
    { required: true, message: 'Please select objective type', trigger: 'change' }
  ],
  value: [
    { required: true, message: 'Please enter objective value', trigger: 'blur' },
    { type: 'number', min: 0, message: 'Value must be positive', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  if (isEditing.value) {
    return 'Edit Objective'
  }
  return selectedRepId.value 
    ? `Add Objective for ${getRepName(selectedRepId.value)}`
    : 'Add New Objective'
})

const availableBrands = computed(() => {
  if (!selectedRepId.value) return brands.value
  
  const rep = representatives.value.find(r => r.id === selectedRepId.value)
  if (!rep) return brands.value
  
  // Return all brands - we can have multiple objectives per brand
  return brands.value
})

// Check if user is admin
const checkAdminStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/is-admin', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    
    if (!response.data.is_admin) {
      ElMessage.error('Access denied: Admin privileges required')
      return false
    }
    return true
  } catch (error) {
    console.error('Failed to check admin status:', error)
    ElMessage.error('Failed to verify admin privileges')
    return false
  }
}

const fetchRepresentatives = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/v1/rep/all', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    // Ensure objectives have proper structure
    representatives.value = response.data.map((rep: any) => ({
      ...rep,
      objectives: rep.objectives || {}
    }))
  } catch (error) {
    console.error('Failed to fetch representatives:', error)
    ElMessage.error('Failed to load representatives')
  } finally {
    loading.value = false
  }
}

const fetchBrands = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/settings/brand')
    brands.value = response.data
  } catch (error) {
    console.error('Failed to fetch brands:', error)
    ElMessage.error('Failed to load brands')
  }
}

const refreshData = async () => {
  await fetchRepresentatives()
}

const showSetObjectiveDialog = (rep?: Representative) => {
  if (rep) {
    selectedRepId.value = rep.id
    formData.rep_id = rep.id
  } else {
    selectedRepId.value = null
    formData.rep_id = ''
  }
  
  editingMode.value = false
  editingContext.value = null
  isEditing.value = false
  resetForm()
  dialogVisible.value = true
}

const editObjective = (rep: Representative, brandName: string, type: 'salesPerCustomer' | 'activeCustomers') => {
  selectedRepId.value = rep.id
  editingMode.value = true
  editingContext.value = { brand_name: brandName, type }
  
  const brandObj = rep.objectives[brandName] || {}
  const value = brandObj[type]
  
  if (value !== undefined) {
    formData.rep_id = rep.id
    formData.brand_name = brandName
    formData.type = type
    formData.value = value
    
    isEditing.value = true
    dialogVisible.value = true
  }
}

const confirmDeleteObjective = async (rep: Representative, brandName: string, type: 'salesPerCustomer' | 'activeCustomers') => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete the ${formatObjectiveType(type)} objective for ${getBrandDisplayName(brandName)}?`,
      'Delete Objective',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )
    
    await deleteObjective(rep.id, brandName, type)
  } catch (error) {
    // User cancelled
  }
}

const deleteObjective = async (repId: string, brandName: string, type: 'salesPerCustomer' | 'activeCustomers') => {
  try {
    await axios.delete('http://localhost:8000/api/v1/settings/objective', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      data: {
        rep_id: repId,
        brand_name: brandName,
        type: type
      }
    })
    
    ElMessage.success('Objective deleted successfully')
    await refreshData()
  } catch (error: any) {
    console.error('Failed to delete objective:', error)
    const errorMsg = error.response?.data?.detail || 'Failed to delete objective'
    ElMessage.error(errorMsg)
  }
}

const getValueLabel = () => {
  if (formData.type === 'salesPerCustomer') {
    return 'Target Sales per Customer (€)'
  } else {
    return 'Target Active Customers Count'
  }
}

const getValuePlaceholder = () => {
  if (formData.type === 'salesPerCustomer') {
    return 'Enter target sales amount in euros'
  } else {
    return 'Enter target number of active customers'
  }
}

const getBrandDisplayName = (brandName: string) => {
  if (brandName === 'ALL') return 'All Brands'
  const brand = brands.value.find(b => b.brand_name === brandName)
  return brand ? brand.showed_brand_name : brandName
}

const getRepName = (repId: string) => {
  const rep = representatives.value.find(r => r.id === repId)
  return rep ? `${rep.key} - ${rep.name || 'No name'}` : ''
}

const formatObjectiveType = (type: string) => {
  const typeMap: Record<string, string> = {
    'salesPerCustomer': 'Sales per Customer',
    'activeCustomers': 'Active Customers'
  }
  return typeMap[type] || type
}

const formatValue = (value: number, type: string) => {
  if (type === 'salesPerCustomer') {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value)
  }
  return value.toLocaleString()
}

const submitForm = async () => {
  if (!objectiveFormRef.value) return
  
  await objectiveFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const payload: any = {
        rep_id: formData.rep_id,
        brand_name: formData.brand_name,
        type: formData.type,
        value: formData.value
      }
      
      // If editing, include the original brand and type for identification
      if (isEditing.value && editingContext.value) {
        payload.original_brand_name = editingContext.value.brand_name
        payload.original_type = editingContext.value.type
      }
      
      await axios.post(
        'http://localhost:8000/api/v1/settings/objective',
        payload,
        {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      ElMessage.success(isEditing.value ? 'Objective updated successfully' : 'Objective set successfully')
      await refreshData()
      handleDialogClose()
    } catch (error: any) {
      console.error('Failed to set objective:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to set objective'
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const resetForm = () => {
  formData.brand_name = ''
  formData.type = 'salesPerCustomer'
  formData.value = 0
  
  if (objectiveFormRef.value) {
    objectiveFormRef.value.clearValidate()
  }
}

const handleDialogClose = () => {
  dialogVisible.value = false
  selectedRepId.value = null
  editingMode.value = false
  editingContext.value = null
  isEditing.value = false
  resetForm()
}

watch(() => selectedRepId.value, (newVal) => {
  if (newVal) {
    formData.rep_id = newVal
  }
})

onMounted(async () => {
  const isAdmin = await checkAdminStatus()
  if (isAdmin) {
    await Promise.all([fetchRepresentatives(), fetchBrands()])
  }
})
</script>

<style scoped>
.objectives-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.objectives-table-card,
.history-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.table-container {
  margin-top: 20px;
}

.objectives-list {
  padding: 8px 0;
}

.no-objectives {
  padding: 4px 0;
}

.objectives-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.objective-item {
  background: #f8f9fa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  transition: background-color 0.2s;
}

.objective-item:hover {
  background: #f0f2f5;
}

.objective-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.objective-actions {
  display: flex;
  gap: 4px;
}

.objective-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.objective-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 4px 0;
}

.detail-info {
  flex: 1;
}

.type-label {
  color: #606266;
  font-weight: 500;
  margin-right: 8px;
}

.type-value {
  color: #409eff;
  font-weight: 600;
}

.no-objective-details {
  padding: 4px 0;
}

.add-another-btn {
  margin-top: 8px;
  padding-left: 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-dialog__body) {
  padding-top: 10px;
}

:deep(.el-table__expanded-cell) {
  padding: 20px !important;
}
</style>