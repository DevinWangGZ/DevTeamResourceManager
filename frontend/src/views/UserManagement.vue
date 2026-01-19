<template>
  <div class="user-management-container">
    <Breadcrumb />
    <el-card>
      <template #header>
        <div class="user-header">
          <h2>用户管理</h2>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建用户
          </el-button>
        </div>
      </template>

      <!-- 筛选栏 -->
      <el-card class="filter-card" shadow="never">
        <el-form :inline="true" :model="filterForm" label-width="80px">
          <el-form-item label="关键词">
            <el-input
              v-model="filterForm.keyword"
              placeholder="搜索用户名、邮箱或姓名"
              clearable
              style="width: 200px"
              @keyup.enter="loadUsers"
            />
          </el-form-item>
          <el-form-item label="角色">
            <el-select
              v-model="filterForm.role"
              placeholder="全部"
              clearable
              style="width: 150px"
            >
              <el-option label="开发人员" value="developer" />
              <el-option label="项目经理" value="project_manager" />
              <el-option label="开发组长" value="development_lead" />
              <el-option label="系统管理员" value="system_admin" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="filterForm.is_active"
              placeholder="全部"
              clearable
              style="width: 120px"
            >
              <el-option label="激活" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadUsers" :icon="Search">搜索</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 用户列表 -->
      <el-card class="user-card" shadow="never" style="margin-top: 20px">
        <el-table :data="userList" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="email" label="邮箱" width="200" />
          <el-table-column prop="full_name" label="姓名" width="120" />
          <el-table-column label="角色" width="200">
            <template #default="{ row }">
              <el-tag
                v-for="roleCode in row.role_codes || []"
                :key="roleCode"
                :type="getRoleTagType(roleCode)"
                style="margin-right: 5px"
              >
                {{ getRoleName(roleCode) }}
              </el-tag>
              <span v-if="!row.role_codes || row.role_codes.length === 0" class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="status_tag" label="状态标签" width="120" />
          <el-table-column label="激活状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '激活' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="editUser(row)">
                编辑
              </el-button>
              <el-button
                link
                type="danger"
                size="small"
                @click="handleDelete(row)"
                :disabled="row.id === userStore.userInfo?.id"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建用户"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="createForm.full_name" placeholder="请输入姓名（可选）" />
        </el-form-item>
        <el-form-item label="角色" prop="role_codes">
          <el-select
            v-model="createForm.role_codes"
            multiple
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="开发人员" value="developer" />
            <el-option label="项目经理" value="project_manager" />
            <el-option label="开发组长" value="development_lead" />
            <el-option label="系统管理员" value="system_admin" />
          </el-select>
          <div class="form-tip">默认密码：12345678（用户首次登录后应修改密码）</div>
        </el-form-item>
        <el-form-item label="激活状态" prop="is_active">
          <el-switch v-model="createForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑用户"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="editForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="状态标签" prop="status_tag">
          <el-input
            v-model="editForm.status_tag"
            placeholder="如：🚀火力全开、💻编码中"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="激活状态" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="handleUpdate">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import {
  getUsers,
  createUser,
  deleteUser,
  updateUserByAdmin,
  type UserInfo,
  type UserCreateParams,
} from '@/api/user'

const userStore = useUserStore()

const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const userList = ref<UserInfo[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filterForm = reactive({
  keyword: '',
  role: '',
  is_active: undefined as boolean | undefined,
})

const showCreateDialog = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<UserCreateParams>({
  username: '',
  email: '',
  full_name: '',
  role_codes: ['developer'],
  is_active: true,
})

const showEditDialog = ref(false)
const editFormRef = ref<FormInstance>()
const editingUser = ref<UserInfo | null>(null)
const editForm = reactive({
  username: '',
  email: '',
  full_name: '',
  status_tag: '',
  is_active: true,
})

const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符之间', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
}

const editRules: FormRules = {
  full_name: [{ max: 100, message: '姓名长度不能超过100个字符', trigger: 'blur' }],
  status_tag: [{ max: 50, message: '状态标签长度不能超过50个字符', trigger: 'blur' }],
}

const getRoleName = (roleCode: string) => {
  const roleMap: Record<string, string> = {
    developer: '开发人员',
    project_manager: '项目经理',
    development_lead: '开发组长',
    system_admin: '系统管理员',
  }
  return roleMap[roleCode] || roleCode
}

const getRoleTagType = (roleCode: string) => {
  const typeMap: Record<string, string> = {
    developer: '',
    project_manager: 'warning',
    development_lead: 'success',
    system_admin: 'danger',
  }
  return typeMap[roleCode] || ''
}

const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    
    if (filterForm.role) {
      params.role = filterForm.role
    }
    if (filterForm.is_active !== undefined) {
      params.is_active = filterForm.is_active
    }
    
    const result = await getUsers(params)
    userList.value = result.items
    
    // 如果有关键词，在前端过滤
    if (filterForm.keyword) {
      const keyword = filterForm.keyword.toLowerCase()
      userList.value = userList.value.filter(
        (user) =>
          user.username.toLowerCase().includes(keyword) ||
          user.email.toLowerCase().includes(keyword) ||
          (user.full_name && user.full_name.toLowerCase().includes(keyword))
      )
    }
    
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.keyword = ''
  filterForm.role = ''
  filterForm.is_active = undefined
  currentPage.value = 1
  loadUsers()
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      try {
        await createUser(createForm)
        ElMessage.success('用户创建成功')
        showCreateDialog.value = false
        loadUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建用户失败')
      } finally {
        creating.value = false
      }
    }
  })
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
  createForm.username = ''
  createForm.email = ''
  createForm.full_name = ''
  createForm.role_codes = ['developer']
  createForm.is_active = true
}

const editUser = (user: UserInfo) => {
  editingUser.value = user
  editForm.username = user.username
  editForm.email = user.email
  editForm.full_name = user.full_name || ''
  editForm.status_tag = user.status_tag || ''
  editForm.is_active = user.is_active
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value || !editingUser.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        await updateUserByAdmin(editingUser.value.id, {
          full_name: editForm.full_name || undefined,
          status_tag: editForm.status_tag || undefined,
          is_active: editForm.is_active,
        })
        ElMessage.success('用户信息更新成功')
        showEditDialog.value = false
        loadUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '更新用户信息失败')
      } finally {
        updating.value = false
      }
    }
  })
}

const resetEditForm = () => {
  editFormRef.value?.resetFields()
  editingUser.value = null
  editForm.username = ''
  editForm.email = ''
  editForm.full_name = ''
  editForm.status_tag = ''
  editForm.is_active = true
}

const handleDelete = async (user: UserInfo) => {
  if (user.id === userStore.userInfo?.id) {
    ElMessage.warning('不能删除自己')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteUser(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadUsers()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadUsers()
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-header h2 {
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.user-card {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.text-muted {
  color: #999;
  font-size: 12px;
}
</style>
