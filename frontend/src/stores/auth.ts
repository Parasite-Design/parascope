import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useSettingsStore } from './settings'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

    const login = async (email: string, password: string) => {
    const response = await axios.post('http://localhost:8000/api/v1/login', {
        email,
        password
    })
    
    token.value = response.data.access_token
    user.value = response.data.user
    
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    
    // Initialize settings after login
    const settingsStore = useSettingsStore()
    settingsStore.initialize()

    return response.data
    }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const isAuthenticated = () => !!token.value

  return { token, user, login, logout, isAuthenticated }
})