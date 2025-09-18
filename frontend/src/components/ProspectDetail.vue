<template>
  <el-dialog
    v-model="visible"
    :title="prospect?.name || 'Prospect Details'"
    width="800px"
    destroy-on-close
  >
    <div v-if="prospect" class="prospect-detail">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Name" min-width="120">
          {{ prospect.name }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Contact Name">
          {{ prospect.contact_name || '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Status">
          <el-tag :type="statusTagType(prospect.status)">
            {{ prospect.status }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="Email">
          <a :href="`mailto:${prospect.email}`">{{ prospect.email }}</a>
        </el-descriptions-item>
        
        <el-descriptions-item label="Phone">
          <a :href="`tel:${prospect.phone}`">{{ prospect.phone }}</a>
        </el-descriptions-item>
        
        <el-descriptions-item label="Address" :span="2">
          {{ prospect.address }}, {{ prospect.city }}, {{ prospect.country }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Prospect Interest">
          <el-rate
            v-model="prospect.prospect_interest"
            disabled
            :max="5"
            show-score
            text-color="#ff9900"
            score-template="{value}"
          />
        </el-descriptions-item>
        
        <el-descriptions-item label="Commercial Interest">
          <el-rate
            v-model="prospect.commercial_interest"
            disabled
            :max="5"
            show-score
            text-color="#ff9900"
            score-template="{value}"
          />
        </el-descriptions-item>
        
        <el-descriptions-item label="Last Visit">
          {{ formatDate(prospect.last_visit) }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Next Visit">
          {{ formatDate(prospect.next_visit) }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Location" :span="2">
          <div v-if="prospect.latitude && prospect.longitude">
            Lat: {{ prospect.latitude }}, Long: {{ prospect.longitude }}
            <el-button 
              type="primary" 
              link 
              @click="openInMaps"
              style="margin-left: 10px;"
            >
              View on Map
            </el-button>
          </div>
          <span v-else>-</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="Notes" :span="2">
          <div class="notes-content">
            {{ prospect.notes || 'No notes available' }}
          </div>
        </el-descriptions-item>
        
        <el-descriptions-item label="Created At">
          {{ formatDateTime(prospect.created_at) }}
        </el-descriptions-item>
        
        <el-descriptions-item label="Last Updated">
          {{ formatDateTime(prospect.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">Close</el-button>
      <el-button type="primary" @click="$emit('update-prospect', prospect)">
        Edit Prospect
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref, watch } from 'vue'

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

const props = defineProps<{
  visible: boolean
  prospect: Prospect | null
}>()

const emit = defineEmits(['update:visible', 'update-prospect'])

const visible = ref(props.visible)
const prospect = ref<Prospect | null>(props.prospect)

watch(() => props.visible, (val) => {
  visible.value = val
})

watch(() => props.prospect, (val) => {
  prospect.value = val
})

watch(visible, (val) => {
  emit('update:visible', val)
})

const statusTagType = (status: string) => {
  const types: { [key: string]: string } = {
    'New': 'info',
    'Pending': 'warning',
    'Lost': 'danger',
    'Converted': 'success',
    'Ready': '',
    'Blocked': 'danger'
  }
  return types[status] || ''
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

const openInMaps = () => {
  if (prospect.value?.latitude && prospect.value?.longitude) {
    window.open(
      `https://www.google.com/maps?q=${prospect.value.latitude},${prospect.value.longitude}`,
      '_blank'
    )
  } else {
    ElMessage.warning('No location data available')
  }
}
</script>

<style scoped>
.prospect-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.notes-content {
  white-space: pre-wrap;
  line-height: 1.5;
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  min-height: 60px;
}

:deep(.el-descriptions__body) {
  background-color: #fff;
}
</style>