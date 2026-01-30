<template>
  <div class="user-management-container">
    <div class="page-header">
      <h1>Account Management</h1>
    </div>

    <!-- Current User Info Card -->
    <el-card class="user-info-card">
      <template #header>
        <div class="card-header">
          <span>My Account</span>
          <el-tag :type="authStore.isAdmin ? 'success' : 'info'" size="small">
            {{ authStore.isAdmin ? 'Administrator' : 'User' }}
          </el-tag>
        </div>
      </template>

      <div class="user-info">
        <div class="info-row">
          <span class="info-label">Email:</span>
          <span class="info-value">{{ authStore.user?.email }}</span>
        </div>
        <div v-if="userRepresentative" class="info-row">
          <span class="info-label">Representative:</span>
          <span class="info-value">{{ userRepresentative.key }} - {{ userRepresentative.name }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Account Created:</span>
          <span class="info-value">{{ formatDate(authStore.user?.created_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Last Updated:</span>
          <span class="info-value">{{ formatDate(authStore.user?.updated_at) }}</span>
        </div>
      </div>
    </el-card>

    <!-- Change Password Card (Available to all users) -->
    <el-card class="change-password-card">
      <template #header>
        <div class="card-header">
          <span>Change Password</span>
        </div>
      </template>

      <div class="form-container">
        <el-form
          ref="changePasswordFormRef"
          :model="changePasswordForm"
          :rules="changePasswordRules"
          label-position="top"
          :disabled="changingPassword"
        >
          <el-form-item label="Current Password" prop="current_password">
            <el-input
              v-model="changePasswordForm.current_password"
              type="password"
              placeholder="Enter current password"
              show-password
            />
          </el-form-item>

          <el-form-item label="New Password" prop="new_password">
            <el-input
              v-model="changePasswordForm.new_password"
              type="password"
              placeholder="Enter new password"
              show-password
            />
          </el-form-item>

          <el-form-item label="Confirm New Password" prop="confirm_password">
            <el-input
              v-model="changePasswordForm.confirm_password"
              type="password"
              placeholder="Confirm new password"
              show-password
            />
          </el-form-item>

          <div class="form-actions">
            <el-button 
              type="primary" 
              @click="submitChangePassword" 
              :loading="changingPassword"
              icon="Key"
            >
              Change Password
            </el-button>
            <el-button @click="resetChangePasswordForm" icon="Refresh">
              Reset
            </el-button>
          </div>
        </el-form>
      </div>
    </el-card>

    <!-- Delete Account Card (Available to all users) -->
    <el-card class="delete-account-card" v-if="!authStore.isAdmin">
      <template #header>
        <div class="card-header">
          <span>Delete Account</span>
        </div>
      </template>

      <div class="danger-zone">
        <p class="warning-text">
          <el-icon><Warning /></el-icon>
          Warning: This action is permanent and cannot be undone. All your data will be lost.
        </p>
        <el-button 
          type="danger" 
          @click="confirmDeleteOwnAccount"
          icon="Delete"
          plain
        >
          Delete My Account
        </el-button>
      </div>
    </el-card>

    <!-- Admin Management Section -->
    <template v-if="authStore.isAdmin">
      <el-divider />
      
      <div class="admin-section-header">
        <h2>Administrator Panel</h2>
        <div class="admin-actions">
          <el-button 
            type="primary" 
            @click="showCreateUserDialog" 
            icon="Plus"
          >
            Create New User
          </el-button>
          <el-button 
            @click="refreshUsers" 
            :loading="loadingUsers"
            icon="Refresh"
          >
            Refresh
          </el-button>
        </div>
      </div>

      <!-- Users Table -->
      <el-card class="users-table-card">
        <template #header>
          <div class="card-header">
            <span>All Users</span>
            <span class="total-count">Total: {{ users.length }}</span>
          </div>
        </template>

        <div class="table-container">
          <el-table 
            :data="users" 
            v-loading="loadingUsers"
            :row-key="(row: { id: any }) => row.id"
            style="width: 100%;"
          >
            <el-table-column prop="email" label="Email" min-width="250" sortable />
            
            <el-table-column prop="is_admin" label="Role" width="120">
              <template #default="{ row }">
                <el-tag :type="row.is_admin ? 'success' : 'info'" size="small">
                  {{ row.is_admin ? 'Admin' : 'User' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="Representative" min-width="200">
              <template #default="{ row }">
                <div v-if="getRepresentativeName(row.representative_id)">
                  {{ getRepresentativeName(row.representative_id) }}
                </div>
                <el-tag v-else type="info" size="small">No rep assigned</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="created_at" label="Created" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column prop="updated_at" label="Updated" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>

            <el-table-column label="Actions" width="250" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button 
                    type="warning" 
                    @click="showResetPasswordDialog(row)" 
                    size="small"
                    icon="Key"
                    title="Reset Password"
                  >
                    Reset PW
                  </el-button>
                  <el-button 
                    v-if="row.id !== authStore.user?.id"
                    type="danger" 
                    @click="confirmDeleteUser(row)" 
                    size="small"
                    icon="Delete"
                    title="Delete User"
                  >
                    Delete
                  </el-button>
                  <el-tag 
                    v-else 
                    type="info" 
                    size="small"
                  >
                    Current User
                  </el-tag>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- Create User Dialog -->
      <el-dialog
        v-model="createUserDialogVisible"
        title="Create New User"
        width="500px"
        :before-close="handleCreateUserDialogClose"
      >
        <el-form
          ref="createUserFormRef"
          :model="createUserForm"
          :rules="createUserRules"
          label-position="top"
          :disabled="creatingUser"
        >
          <el-form-item label="Email" prop="email">
            <el-input
              v-model="createUserForm.email"
              placeholder="Enter email address"
              type="email"
            />
          </el-form-item>

          <el-form-item label="Password" prop="password">
            <el-input
              v-model="createUserForm.password"
              type="password"
              placeholder="Enter password"
              show-password
            />
          </el-form-item>

          <el-form-item label="Confirm Password" prop="confirmPassword">
            <el-input
              v-model="createUserForm.confirmPassword"
              type="password"
              placeholder="Confirm password"
              show-password
            />
          </el-form-item>

          <el-form-item label="Administrator" prop="is_admin">
            <el-switch
              v-model="createUserForm.is_admin"
              active-text="Admin"
              inactive-text="User"
            />
          </el-form-item>

          <el-form-item label="Representative" prop="representative_id">
            <el-select
              v-model="createUserForm.representative_id"
              placeholder="Select representative (optional)"
              filterable
              style="width: 100%;"
              clearable
            >
              <el-option
                v-for="rep in availableRepresentatives"
                :key="rep.code"
                :label="`${rep.code} - ${rep.key} - ${rep.name || 'No name'}`"
                :value="rep.code"
              />
              <el-option
                label="No representative"
                :value="null"
              />
            </el-select>
            <div class="form-help">
              Assigning a representative links this user to a specific rep
            </div>
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleCreateUserDialogClose" :disabled="creatingUser">
              Cancel
            </el-button>
            <el-button 
              type="primary" 
              @click="submitCreateUser" 
              :loading="creatingUser"
            >
              Create User
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- Reset Password Dialog -->
      <el-dialog
        v-model="resetPasswordDialogVisible"
        :title="`Reset Password for ${resetPasswordUser?.email}`"
        width="400px"
        :before-close="handleResetPasswordDialogClose"
      >
        <el-form
          ref="resetPasswordFormRef"
          :model="resetPasswordForm"
          :rules="resetPasswordRules"
          label-position="top"
          :disabled="resettingPassword"
        >
          <el-form-item label="New Password" prop="new_password">
            <el-input
              v-model="resetPasswordForm.new_password"
              type="password"
              placeholder="Enter new password"
              show-password
            />
          </el-form-item>

          <el-form-item label="Confirm New Password" prop="confirm_password">
            <el-input
              v-model="resetPasswordForm.confirm_password"
              type="password"
              placeholder="Confirm new password"
              show-password
            />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleResetPasswordDialogClose" :disabled="resettingPassword">
              Cancel
            </el-button>
            <el-button 
              type="primary" 
              @click="submitResetPassword" 
              :loading="resettingPassword"
            >
              Reset Password
            </el-button>
          </span>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { api, useAuthStore } from '../stores/auth'

interface User {
  id: string
  email: string
  is_admin: boolean
  representative_id: string | null
  created_at: string
  updated_at: string
}

interface Representative {
  id: string
  code: number
  key: string
  name: string
  objectives: Record<string, any>
}

interface ChangePasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

interface CreateUserForm {
  email: string
  password: string
  confirmPassword: string
  is_admin: boolean
  representative_id: number | null
}

interface ResetPasswordForm {
  new_password: string
  confirm_password: string
}

const authStore = useAuthStore()

// State
const users = ref<User[]>([])
const representatives = ref<Representative[]>([])
const loadingUsers = ref(false)
const changingPassword = ref(false)
const creatingUser = ref(false)
const resettingPassword = ref(false)

// Dialog visibility
const createUserDialogVisible = ref(false)
const resetPasswordDialogVisible = ref(false)

// Current user for reset password
const resetPasswordUser = ref<User | null>(null)

// Forms
const changePasswordFormRef = ref<FormInstance>()
const changePasswordForm = reactive<ChangePasswordForm>({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const createUserFormRef = ref<FormInstance>()
const createUserForm = reactive<CreateUserForm>({
  email: '',
  password: '',
  confirmPassword: '',
  is_admin: false,
  representative_id: null
})

const resetPasswordFormRef = ref<FormInstance>()
const resetPasswordForm = reactive<ResetPasswordForm>({
  new_password: '',
  confirm_password: ''
})

// Validation rules
const changePasswordRules: FormRules = {
  current_password: [
    { required: true, message: 'Please enter current password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: 'Please enter new password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
    { validator: validateNewPassword, trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: 'Please confirm new password', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const createUserRules: FormRules = {
  email: [
    { required: true, message: 'Please enter email address', trigger: 'blur' },
    { type: 'email', message: 'Please enter valid email', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    { validator: validateCreateUserConfirmPassword, trigger: 'blur' }
  ],
  representative_id: [
    { validator: validateRepresentativeId, trigger: 'change' }
  ]
}

const resetPasswordRules: FormRules = {
  new_password: [
    { required: true, message: 'Please enter new password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: 'Please confirm new password', trigger: 'blur' },
    { validator: validateResetPasswordConfirm, trigger: 'blur' }
  ]
}

// Validators
function validateNewPassword(rule: any, value: string, callback: Function) {
  if (value === changePasswordForm.current_password) {
    callback(new Error('New password must be different from current password'))
  } else {
    callback()
  }
}

function validateConfirmPassword(rule: any, value: string, callback: Function) {
  if (value !== changePasswordForm.new_password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

function validateCreateUserConfirmPassword(rule: any, value: string, callback: Function) {
  if (value !== createUserForm.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

function validateResetPasswordConfirm(rule: any, value: string, callback: Function) {
  if (value !== resetPasswordForm.new_password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

function validateRepresentativeId(rule: any, value: string | null, callback: Function) {
  // Representative is optional, so always valid
  callback()
}

// Computed properties
const userRepresentative = computed(() => {
  if (!authStore.user?.representative_id) return null
  return representatives.value.find(rep => rep.id === authStore.user?.representative_id)
})

const availableRepresentatives = computed(() => {
  // Filter out representatives that already have a user assigned
  const assignedRepIds = users.value
    .map(user => user.representative_id)
    .filter(id => id !== null) as string[]
  
  return representatives.value.filter(rep => !assignedRepIds.includes(rep.id))
})

// Methods
const fetchUsers = async () => {
  if (!authStore.isAdmin) return
  
  loadingUsers.value = true
  try {
    const response = await api.get('http://localhost:8000/api/v1/users', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    users.value = response.data
  } catch (error) {
    console.error('Failed to fetch users:', error)
    ElMessage.error('Failed to load users')
  } finally {
    loadingUsers.value = false
  }
}

const fetchRepresentatives = async () => {
  try {
    const response = await api.get('http://localhost:8000/api/v1/rep/all', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    representatives.value = response.data
  } catch (error) {
    console.error('Failed to fetch representatives:', error)
    ElMessage.error('Failed to load representatives')
  }
}

const refreshUsers = async () => {
  if (authStore.isAdmin) {
    await Promise.all([fetchUsers(), fetchRepresentatives()])
  }
}

const getRepresentativeName = (representativeId: string | null) => {
  if (!representativeId) return ''
  const rep = representatives.value.find(r => r.id === representativeId)
  return rep ? `${rep.key} - ${rep.name}` : ''
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Change Password
const submitChangePassword = async () => {
  if (!changePasswordFormRef.value) return
  
  await changePasswordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    changingPassword.value = true
    try {
      await api.post(
        'http://localhost:8000/api/v1/change-password',
        {
          current_password: changePasswordForm.current_password,
          new_password: changePasswordForm.new_password
        },
        {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      ElMessage.success('Password changed successfully')
      resetChangePasswordForm()
    } catch (error: any) {
      console.error('Failed to change password:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to change password'
      ElMessage.error(errorMsg)
    } finally {
      changingPassword.value = false
    }
  })
}

const resetChangePasswordForm = () => {
  changePasswordForm.current_password = ''
  changePasswordForm.new_password = ''
  changePasswordForm.confirm_password = ''
  
  if (changePasswordFormRef.value) {
    changePasswordFormRef.value.clearValidate()
  }
}

// Create User (Admin only)
const showCreateUserDialog = () => {
  createUserForm.email = ''
  createUserForm.password = ''
  createUserForm.confirmPassword = ''
  createUserForm.is_admin = false
  createUserForm.representative_id = null
  
  if (createUserFormRef.value) {
    createUserFormRef.value.clearValidate()
  }
  
  createUserDialogVisible.value = true
}

const submitCreateUser = async () => {
  if (!createUserFormRef.value) return
  
  await createUserFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    creatingUser.value = true
    try {
      await api.post(
        'http://localhost:8000/api/v1/register',
        {
          email: createUserForm.email,
          password: createUserForm.password,
          is_admin: createUserForm.is_admin,
          representative_id: createUserForm.representative_id
        },
        {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      ElMessage.success('User created successfully')
      await fetchUsers()
      handleCreateUserDialogClose()
    } catch (error: any) {
      console.error('Failed to create user:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to create user'
      ElMessage.error(errorMsg)
    } finally {
      creatingUser.value = false
    }
  })
}

const handleCreateUserDialogClose = () => {
  createUserDialogVisible.value = false
}

// Reset Password (Admin only)
const showResetPasswordDialog = (user: User) => {
  resetPasswordUser.value = user
  resetPasswordForm.new_password = ''
  resetPasswordForm.confirm_password = ''
  
  if (resetPasswordFormRef.value) {
    resetPasswordFormRef.value.clearValidate()
  }
  
  resetPasswordDialogVisible.value = true
}

const submitResetPassword = async () => {
  if (!resetPasswordFormRef.value || !resetPasswordUser.value) return
  
  await resetPasswordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    resettingPassword.value = true
    try {
      await api.post(
        'http://localhost:8000/api/v1/reset-password',
        {
          user_id: resetPasswordUser.value?.id,
          new_password: resetPasswordForm.new_password
        },
        {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      ElMessage.success('Password reset successfully')
      handleResetPasswordDialogClose()
    } catch (error: any) {
      console.error('Failed to reset password:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to reset password'
      ElMessage.error(errorMsg)
    } finally {
      resettingPassword.value = false
    }
  })
}

const handleResetPasswordDialogClose = () => {
  resetPasswordDialogVisible.value = false
  resetPasswordUser.value = null
}

// Delete Account
const confirmDeleteOwnAccount = async () => {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete your account? This action is permanent and cannot be undone. All your data will be lost.',
      'Delete Account',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await deleteAccount()
  } catch (error) {
    // User cancelled
  }
}

const confirmDeleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete user "${user.email}"? This action is permanent and cannot be undone.`,
      'Delete User',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await deleteAccount(user.id)
  } catch (error) {
    // User cancelled
  }
}

const deleteAccount = async (userId?: string) => {
  try {
    const params = userId ? { user_id: userId } : {}
    
    await api.delete('http://localhost:8000/api/v1/delete-account', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      params
    })
    
    if (userId) {
      ElMessage.success('User deleted successfully')
      await fetchUsers()
    } else {
      ElMessage.success('Your account has been deleted')
      // Redirect to logout or login page
      // In a real app, you'd want to log the user out and redirect
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
    }
  } catch (error: any) {
    console.error('Failed to delete account:', error)
    const errorMsg = error.response?.data?.detail || 'Failed to delete account'
    ElMessage.error(errorMsg)
  }
}

// Lifecycle
onMounted(async () => {
  await fetchRepresentatives()
  if (authStore.isAdmin) {
    await fetchUsers()
  }
})
</script>

<style scoped>
.user-management-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.user-info-card,
.change-password-card,
.delete-account-card,
.users-table-card {
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

.user-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #303133;
  min-width: 140px;
}

.info-value {
  color: #606266;
  flex: 1;
}

.form-container {
  padding: 20px 0;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.danger-zone {
  padding: 20px;
  text-align: center;
}

.warning-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #f56c6c;
  margin-bottom: 20px;
  font-weight: 500;
}

.admin-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 32px 0 16px 0;
}

.admin-actions {
  display: flex;
  gap: 10px;
}

.table-container {
  margin-top: 20px;
}

.total-count {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-input) {
  width: 100%;
}

:deep(.el-dialog__body) {
  padding-top: 10px;
}

:deep(.el-divider) {
  margin: 32px 0;
}
</style>