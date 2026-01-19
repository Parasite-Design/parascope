<template>
  <el-dialog
    v-model="visible"
    :title="mode === 'create' ? 'Create New Prospect' : 'Edit Prospect'"
    width="700px"
    destroy-on-close
  >
    <el-steps :active="activeStep" simple>
      <el-step title="Basic Info" />
      <el-step title="Contact Details" />
      <el-step title="Brands & Interest" />
      <el-step title="Review" />
    </el-steps>

    <el-form 
      :model="form" 
      :rules="rules" 
      ref="formRef" 
      label-width="140px"
      label-position="top"
      style="margin-top: 20px;"
    >
      <!-- Step 1: Basic Info -->
      <div v-if="activeStep === 0">
        <el-form-item label="Prospect Name" prop="name">
          <el-input v-model="form.name" placeholder="Enter prospect name" />
        </el-form-item>
        
        <el-form-item label="Contact Person" prop="contact_name">
          <el-input v-model="form.contact_name" placeholder="Enter contact person name" />
        </el-form-item>
        
        <el-form-item label="Status" prop="status">
          <el-select v-model="form.status" placeholder="Select status">
            <el-option
              v-for="status in statusOptions"
              :key="status"
              :label="status"
              :value="status"
            />
          </el-select>
        </el-form-item>
      </div>

      <!-- Step 2: Contact Details -->
      <div v-if="activeStep === 1">
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" type="email" placeholder="Enter email address" />
        </el-form-item>
        
        <el-form-item label="Phone" prop="phone">
          <el-input v-model="form.phone" placeholder="Enter phone number" />
        </el-form-item>
        
        <el-form-item label="Address" prop="address">
          <el-input v-model="form.address" placeholder="Enter street address" />
        </el-form-item>
        
        <el-form-item label="City" prop="city">
          <el-input v-model="form.city" placeholder="Enter city" />
        </el-form-item>
        
        <el-form-item label="Postal Code" prop="postal_code">
          <el-input v-model="form.postal_code" placeholder="Enter postal code" />
        </el-form-item>
        
        <el-form-item label="Country" prop="country">
          <el-input v-model="form.country" placeholder="Enter country" />
        </el-form-item>
      </div>

      <!-- Step 3: Brands & Interest -->
      <div v-if="activeStep === 2">
        <el-form-item label="Brands" prop="brands">
          <el-select
            v-model="form.brands"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            placeholder="Type or select brands"
            style="width: 100%;"
          >
            <el-option
              v-for="brand in availableBrands"
              :key="brand.brand_name"
              :label="brand.showed_brand_name"
              :value="brand.brand_name"
            />
          </el-select>
          <div class="form-hint">
            Type to search or select from available brands
          </div>
        </el-form-item>
        
        <el-form-item label="Prospect Interest (0-5)" prop="prospect_interest">
          <el-rate
            v-model="form.prospect_interest"
            :max="5"
            show-text
            :texts="['Very Low', 'Low', 'Medium', 'High', 'Very High']"
          />
        </el-form-item>
        
        <el-form-item label="Commercial Interest (0-5)" prop="commercial_interest">
          <el-rate
            v-model="form.commercial_interest"
            :max="5"
            show-text
            :texts="['Very Low', 'Low', 'Medium', 'High', 'Very High']"
          />
        </el-form-item>
        
        <el-form-item label="Notes" prop="notes">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="4"
            placeholder="Add any additional notes"
          />
        </el-form-item>
        
        <el-form-item label="Favorite" prop="favorite">
          <el-switch v-model="form.favorite" />
        </el-form-item>
      </div>

      <!-- Step 4: Review -->
      <div v-if="activeStep === 3">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Name">{{ form.name }}</el-descriptions-item>
          <el-descriptions-item label="Contact">{{ form.contact_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Status">{{ form.status }}</el-descriptions-item>
          <el-descriptions-item label="Email">{{ form.email }}</el-descriptions-item>
          <el-descriptions-item label="Phone">{{ form.phone }}</el-descriptions-item>
          <el-descriptions-item label="Address">{{ form.address }}, {{ form.city }}, {{ form.postal_code }}, {{ form.country }}</el-descriptions-item>
          <el-descriptions-item label="Brands">
            <div class="brands-review">
              <el-tag
                v-for="brand in form.brands"
                :key="brand"
                size="small"
                style="margin-right: 4px; margin-bottom: 4px;"
              >
                {{ getBrandDisplayName(brand) }}
              </el-tag>
              <span v-if="!form.brands || form.brands.length === 0">-</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="Prospect Interest">{{ form.prospect_interest }}/5</el-descriptions-item>
          <el-descriptions-item label="Commercial Interest">{{ form.commercial_interest }}/5</el-descriptions-item>
          <el-descriptions-item label="Overall Interest">{{ form.prospect_interest + form.commercial_interest }}/10</el-descriptions-item>
          <el-descriptions-item label="Notes">{{ form.notes || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Favorite">{{ form.favorite ? 'Yes' : 'No' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="prevStep" :disabled="activeStep === 0">
        Previous
      </el-button>
      <el-button 
        @click="nextStep" 
        :disabled="activeStep === 3"
        type="primary"
      >
        Next
      </el-button>
      <el-button 
        v-if="activeStep === 3" 
        type="success" 
        @click="submitForm"
        :loading="submitting"
      >
        {{ mode === 'create' ? 'Create Prospect' : 'Update Prospect' }}
      </el-button>
      <el-button @click="visible = false">Cancel</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

interface Brand {
  brand_name: string
  showed_brand_name: string
}

interface Prospect {
  id?: string
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
}

const props = defineProps<{
  visible: boolean
  prospect: Prospect | null
  mode: 'create' | 'edit'
  availableBrands: Brand[]
}>()

const emit = defineEmits(['update:visible', 'saved', 'closed'])

const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const activeStep = ref(0)
const submitting = ref(false)

const statusOptions = ['New', 'Pending', 'Lost', 'Converted', 'Ready', 'Blocked']

const form = reactive<Prospect>({
  name: '',
  contact_name: '',
  status: 'New',
  notes: '',
  phone: '',
  email: '',
  city: '',
  country: '',
  postal_code: '',
  address: '',
  prospect_interest: 3,
  commercial_interest: 3,
  last_visit: null,
  next_visit: null,
  latitude: null,
  longitude: null,
  brands: [],
  favorite: false
})

const rules = reactive<FormRules>({
  name: [{ required: true, message: 'Please input prospect name', trigger: 'blur' }],
  email: [
    { required: true, message: 'Please input email address', trigger: 'blur' },
    { type: 'email', message: 'Please input valid email', trigger: 'blur' }
  ],
  phone: [{ required: true, message: 'Please input phone number', trigger: 'blur' }],
  city: [{ required: true, message: 'Please input city', trigger: 'blur' }],
  country: [{ required: true, message: 'Please input country', trigger: 'blur' }],
  address: [{ required: true, message: 'Please input address', trigger: 'blur' }],
  status: [{ required: true, message: 'Please select status', trigger: 'change' }]
})

const visible = ref(props.visible)

const getBrandDisplayName = (brandName: string): string => {
  const brand = props.availableBrands.find(b => b.brand_name === brandName)
  return brand ? brand.showed_brand_name : brandName
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    resetForm()
    if (props.prospect) {
      Object.assign(form, props.prospect)
    }
  }
})

watch(visible, (val) => {
  if (!val) {
    emit('closed')
  }
  emit('update:visible', val)
})

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  activeStep.value = 0
  Object.assign(form, {
    name: '',
    contact_name: '',
    status: 'New',
    notes: '',
    phone: '',
    email: '',
    city: '',
    country: '',
    postal_code: '',
    address: '',
    prospect_interest: 3,
    commercial_interest: 3,
    last_visit: null,
    next_visit: null,
    latitude: null,
    longitude: null,
    brands: [],
    favorite: false
  })
}

const nextStep = async () => {
  if (formRef.value) {
    try {
      await formRef.value.validate()
      activeStep.value++
    } catch (error) {
      ElMessage.warning('Please complete all required fields')
    }
  }
}

const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

const submitForm = async () => {
  if (formRef.value) {
    try {
      submitting.value = true
      await formRef.value.validate()
      
      const payload = {
        ...form,
        // Ensure brands is an array
        brands: Array.isArray(form.brands) ? form.brands : []
      }
      
      if (props.mode === 'create') {
        await axios.post(
          'http://localhost:8000/api/v1/prospect/',
          payload,
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        )
      } else {
        await axios.put(
          `http://localhost:8000/api/v1/prospect/${form.id}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        )
      }
      
      emit('saved')
      visible.value = false
    } catch (error) {
      console.error('Failed to save prospect:', error)
      ElMessage.error('Failed to save prospect')
    } finally {
      submitting.value = false
    }
  }
}
</script>

<style scoped>
.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.brands-review {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>