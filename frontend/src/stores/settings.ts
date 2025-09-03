import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

interface Brand {
  brand_name: string
  showed_brand_name: string
}

interface Period {
  period_start: string
  period_end: string
}

export const useSettingsStore = defineStore('settings', () => {
  const authStore = useAuthStore()
  
  const selectedBrand = ref<string>(localStorage.getItem('selectedBrand') || '')
  const selectedPeriodType = ref<string>(localStorage.getItem('selectedPeriodType') || 'fiscal')
  const customPeriodStart = ref<string>(localStorage.getItem('customPeriodStart') || '')
  const customPeriodEnd = ref<string>(localStorage.getItem('customPeriodEnd') || '')
  const brands = ref<Brand[]>([])
  const period = ref<Period>({ period_start: '', period_end: '' })
  
  const fetchBrands = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/settings/brand', {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      })
      brands.value = response.data
    } catch (error) {
      console.error('Failed to fetch brands:', error)
    }
  }
  
  const fetchPeriod = async (periodType: string) => {
    try {
      let endpoint
      if (periodType === 'rolling') {
        endpoint = '/api/v1/dates/rolling-year'
      } else if (periodType === 'fiscal') {
        endpoint = '/api/v1/dates/n/-1'
      } else {
        // For custom period, we don't fetch from API
        return
      }
      
      const response = await axios.get(`http://localhost:8000${endpoint}`, {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      })
      
      period.value = response.data
      selectedPeriodType.value = periodType
      
      // Save to localStorage
      localStorage.setItem('selectedPeriodType', periodType)
    } catch (error) {
      console.error('Failed to fetch period:', error)
    }
  }
  
  const setCustomPeriod = (start: string, end: string) => {
    customPeriodStart.value = start
    customPeriodEnd.value = end
    selectedPeriodType.value = 'custom'
    period.value = { period_start: start, period_end: end }
    
    // Save to localStorage
    localStorage.setItem('customPeriodStart', start)
    localStorage.setItem('customPeriodEnd', end)
    localStorage.setItem('selectedPeriodType', 'custom')
  }
  
  const setBrand = (brandName: string) => {
    selectedBrand.value = brandName
    localStorage.setItem('selectedBrand', brandName)
  }
  
  // Initialize from localStorage
  const initialize = () => {
    if (selectedPeriodType.value === 'custom' && customPeriodStart.value && customPeriodEnd.value) {
      period.value = {
        period_start: customPeriodStart.value,
        period_end: customPeriodEnd.value
      }
    } else if (selectedPeriodType.value && selectedPeriodType.value !== 'custom') {
      fetchPeriod(selectedPeriodType.value)
    }
    
    if (authStore.isAuthenticated()) {
      fetchBrands()
    }
  }
  
  return {
    selectedBrand,
    selectedPeriodType,
    customPeriodStart,
    customPeriodEnd,
    brands,
    period,
    fetchBrands,
    fetchPeriod,
    setCustomPeriod,
    setBrand,
    initialize
  }
})