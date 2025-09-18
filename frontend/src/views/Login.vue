<template>
  <div class="login-container">
    <div class="login-background"></div>
    
    <div class="login-content">
      <div class="login-box">
        <div class="logo-container">
          <img :src="logo" alt="Company Logo" class="logo" />
          <h1 class="company-name">I-VISION</h1>
        </div>

        <el-card shadow="always" class="login-form-card">
          <h2 class="login-title">Welcome Back</h2>
          <p class="login-subtitle">Please enter your credentials to access your account</p>

          <el-form 
            @submit.prevent="handleLogin" 
            :model="form" 
            :rules="rules" 
            ref="loginForm"
            class="login-form"
          >
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="Email address"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="Password"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-button 
              type="primary" 
              native-type="submit" 
              :loading="loading"
              class="login-button"
              size="large"
            >
              Sign In
            </el-button>

            <div class="login-links">
              <a href="#" class="forgot-link">Forgot password?</a>
            </div>
          </el-form>
        </el-card>

        <div class="login-footer">
          <p>© 2025 Parasite Eyewear. All rights reserved.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

// Import your assets (make sure to add these files to your assets folder)
import backgroundImage from '@/assets/login_background.png'
import logo from '@/assets/logo.jpeg'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: ''
})

const rules = reactive<FormRules>({
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email address', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ]
})

const loading = ref(false)
const loginForm = ref<FormInstance>()

const handleLogin = async () => {
  if (!loginForm.value) return
  
  const valid = await loginForm.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    ElMessage.success('Login successful!')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Login failed. Please check your credentials.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('@/assets/login_background.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: brightness(0.4);
  z-index: 0;
}

.login-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1;
  overflow-y: auto;
  padding: 20px;
  box-sizing: border-box;
}

.login-box {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: auto;
}

.logo-container {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  height: 80px;
  width: auto;
  margin-bottom: 16px;
}

.company-name {
  color: white;
  font-size: 28px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.5px;
}

.login-form-card {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  border: none;
}

.login-form-card :deep(.el-card__body) {
  padding: 30px;
}

.login-title {
  text-align: center;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.login-subtitle {
  text-align: center;
  margin: 0 0 24px 0;
  color: #606266;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

.login-button {
  width: 100%;
  margin-top: 10px;
  font-weight: 600;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  border: none;
}

.login-button:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2c6db3 100%);
  box-shadow: 0 4px 12px rgba(51, 126, 204, 0.4);
}

.login-links {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.forgot-link {
  color: #409EFF;
  text-decoration: none;
  font-size: 14px;
}

.forgot-link:hover {
  text-decoration: underline;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
}

.login-footer p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin: 0;
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .login-box {
    max-width: 100%;
  }
  
  .login-form-card :deep(.el-card__body) {
    padding: 20px;
  }
  
  .logo {
    height: 60px;
  }
  
  .company-name {
    font-size: 24px;
  }
}
</style>