<template>
  <div class="brands-container">
    <div class="page-header">
      <h1>Brand Management</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateForm" icon="Plus">
          Add Brand
        </el-button>
      </div>
    </div>

    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>Brands List</span>
          <el-input
            v-model="searchQuery"
            placeholder="Search brands..."
            clearable
            style="width: 250px;"
            @clear="applyFilters"
            @keyup.enter="applyFilters"
          >
            <template #suffix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table
        :data="filteredBrands"
        v-loading="loading"
        style="width: 100%"
        stripe
        empty-text="No brands found"
      >
        <el-table-column prop="brand_name" label="Brand Code" sortable width="180">
          <template #default="{ row }">
            <span class="brand-code">{{ row.brand_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="showed_brand_name" label="Display Name" sortable min-width="200">
          <template #default="{ row }">
            <span class="display-name">{{ row.showed_brand_name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteBrand(row)" 
              icon="Delete"
            >
              Delete
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Brand Form Dialog -->
    <el-dialog
      v-model="formVisible"
      :title="formMode === 'create' ? 'Add New Brand' : 'Edit Brand'"
      width="500px"
    >
      <el-form
        ref="brandFormRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
      >
        <el-form-item label="Brand Code" prop="brand_name">
          <el-input
            v-model="formData.brand_name"
            placeholder="Enter brand code (e.g., PARASITE)"
            :disabled="formMode === 'edit'"
          />
          <div class="form-hint">
            This is the internal code used in the system
          </div>
        </el-form-item>

        <el-form-item label="Display Name" prop="showed_brand_name">
          <el-input
            v-model="formData.showed_brand_name"
            placeholder="Enter display name (e.g., Parasite)"
          />
          <div class="form-hint">
            This is the name shown to users
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelForm">Cancel</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ formMode === 'create' ? 'Create' : 'Update' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth'

interface Brand {
  brand_name: string
  showed_brand_name: string
}

const authStore = useAuthStore()

const brands = ref<Brand[]>([])
const filteredBrands = ref<Brand[]>([])
const loading = ref(false)
const searchQuery = ref('')
const formVisible = ref(false)
const submitting = ref(false)
const formMode = ref<'create' | 'edit'>('create')

const brandFormRef = ref<FormInstance>()
const formData = reactive({
  brand_name: '',
  showed_brand_name: ''
})

const formRules: FormRules = {
  brand_name: [
    { required: true, message: 'Brand code is required', trigger: 'blur' },
    { min: 2, message: 'Brand code must be at least 2 characters', trigger: 'blur' }
  ],
  showed_brand_name: [
    { required: true, message: 'Display name is required', trigger: 'blur' },
    { min: 2, message: 'Display name must be at least 2 characters', trigger: 'blur' }
  ]
}

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
      // Redirect or show error page
      return false
    }
    return true
  } catch (error) {
    console.error('Failed to check admin status:', error)
    ElMessage.error('Failed to verify admin privileges')
    return false
  }
}

const fetchBrands = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/v1/settings/brand')
    brands.value = response.data
    filteredBrands.value = response.data
  } catch (error) {
    console.error('Failed to fetch brands:', error)
    ElMessage.error('Failed to load brands')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  if (!searchQuery.value) {
    filteredBrands.value = brands.value
    return
  }
  
  const query = searchQuery.value.toLowerCase()
  filteredBrands.value = brands.value.filter(brand => 
    brand.brand_name.toLowerCase().includes(query) ||
    brand.showed_brand_name.toLowerCase().includes(query)
  )
}

const showCreateForm = () => {
  formMode.value = 'create'
  formData.brand_name = ''
  formData.showed_brand_name = ''
  formVisible.value = true
  
  // Reset validation
  nextTick(() => {
    brandFormRef.value?.clearValidate()
  })
}

const submitForm = async () => {
  if (!brandFormRef.value) return
  
  await brandFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (formMode.value === 'create') {
        await axios.post(
          'http://localhost:8000/api/v1/settings/brand',
          {
            brand_name: formData.brand_name,
            showed_brand_name: formData.showed_brand_name
          },
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        ElMessage.success('Brand created successfully')
      } else {
        // For edit, we need to delete old and create new since API only has POST/DELETE
        // Or if your API supports PUT, use that instead
        ElMessage.warning('Edit functionality requires update endpoint')
      }
      
      formVisible.value = false
      fetchBrands()
    } catch (error: any) {
      console.error('Failed to save brand:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to save brand'
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const deleteBrand = async (brand: Brand) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete brand "${brand.showed_brand_name}" (${brand.brand_name})? This action cannot be undone.`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await axios.delete(
      `http://localhost:8000/api/v1/settings/brand/${brand.brand_name}`,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      }
    )
    
    ElMessage.success('Brand deleted successfully')
    fetchBrands()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete brand:', error)
      ElMessage.error('Failed to delete brand')
    }
  }
}

const cancelForm = () => {
  formVisible.value = false
}

onMounted(async () => {
  const isAdmin = await checkAdminStatus()
  if (isAdmin) {
    fetchBrands()
  }
})
</script>

<style scoped>
.brands-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.table-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 600;
  color: #409EFF;
}

.display-name {
  font-weight: 500;
  color: #303133;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>