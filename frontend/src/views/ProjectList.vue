<template>
  <div class="project-list-container">
    <Breadcrumb />
    <div class="project-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreateDialog = true" v-if="canCreate">
        <el-icon><Plus /></el-icon>
        创建项目
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" label-width="80px">
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索项目名称或描述"
            clearable
            style="width: 200px"
            @keyup.enter="loadProjects"
          />
        </el-form-item>
        <el-form-item label="创建者" v-if="canViewAll">
          <el-select
            v-model="filterForm.creator_id"
            placeholder="全部"
            clearable
            filterable
            style="width: 150px"
            :loading="userLoading"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.full_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadProjects" :icon="Search">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 项目列表 -->
    <el-card class="project-card">
      <el-table :data="projectList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="description" label="项目描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="estimated_output_value" label="预计产值（元）" width="150" align="right">
          <template #default="{ row }">
            <span v-if="row.estimated_output_value">
              {{ formatMoney(row.estimated_output_value) }}
            </span>
            <span v-else class="text-placeholder">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewProject(row.id)">
              查看
            </el-button>
            <el-button
              v-if="canViewTasks(row)"
              link
              type="success"
              size="small"
              @click="viewProjectTasks(row.id)"
            >
              任务执行
            </el-button>
            <el-button
              v-if="canViewTasks(row)"
              link
              type="info"
              size="small"
              @click="viewProjectProgress(row.id)"
            >
              进展数据
            </el-button>
            <el-button
              v-if="canEdit(row)"
              link
              type="warning"
              size="small"
              @click="showEditDialogFunc(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="canDelete(row)"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadProjects"
          @current-change="loadProjects"
        />
      </div>
    </el-card>

    <!-- 创建项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建项目"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="120px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="预计产值（元）" prop="estimated_output_value">
          <el-input-number
            v-model="createForm.estimated_output_value"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="项目立项时填写"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑项目对话框 -->
    <el-dialog
      v-model="showEditDialogFlag"
      title="编辑项目"
      width="600px"
      @close="resetEditForm"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="120px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="预计产值（元）" prop="estimated_output_value">
          <el-input-number
            v-model="editForm.estimated_output_value"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="项目立项时填写"
          />
        </el-form-item>
        <el-form-item v-if="canManageCoManagersInEdit" label="协办项目经理">
          <el-select
            v-model="editManagerIds"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="可多选项目经理，与创建者权限一致（任务执行、进展统计等）"
            style="width: 100%"
            :loading="pmUserLoading"
          >
            <el-option
              v-for="u in pmCandidates"
              :key="u.id"
              :disabled="u.id === currentEditProject?.created_by"
              :label="u.full_name ? `${u.full_name}（${u.username}）` : u.username"
              :value="u.id"
            />
          </el-select>
          <span class="form-hint">仅项目创建者与系统管理员可维护此项</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialogFlag = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getProjects,
  createProject,
  updateProject,
  updateProjectManagers,
  deleteProject,
  getProject,
  type Project,
  type ProjectCreate,
  type ProjectUpdate,
} from '@/api/project'
import { getUsers, type UserInfo } from '@/api/user'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const projectList = ref<Project[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const filterForm = reactive({
  keyword: '',
  creator_id: undefined as number | undefined,
})

const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<ProjectCreate>({
  name: '',
  description: '',
  estimated_output_value: undefined,
})

const showEditDialogFlag = ref(false)
const editLoading = ref(false)
const editFormRef = ref<FormInstance>()
const currentEditProject = ref<Project | null>(null)
const editForm = reactive<ProjectUpdate>({
  name: '',
  description: '',
  estimated_output_value: undefined,
})

const editManagerIds = ref<number[]>([])
const pmCandidates = ref<UserInfo[]>([])
const pmUserLoading = ref(false)

const loadPmCandidates = async () => {
  pmUserLoading.value = true
  try {
    const r = await getUsers({ limit: 1000, role: 'project_manager', is_active: true })
    pmCandidates.value = r.items
  } finally {
    pmUserLoading.value = false
  }
}

const canManageCoManagersInEdit = computed(() => {
  if (!currentEditProject.value) return false
  if (userStore.hasRole('system_admin')) return true
  return currentEditProject.value.created_by === userStore.userInfo?.id
})

// 用户列表（用于筛选）
const userList = ref<UserInfo[]>([])
const userLoading = ref(false)

const createRules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

const editRules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

// 权限判断
const canCreate = computed(() => {
  return userStore.hasAnyRole('project_manager', 'system_admin')
})

const canViewAll = computed(() => {
  return userStore.hasAnyRole('development_lead', 'system_admin')
})

/** 是否为该项目的项目经理（创建者或协办） */
const isPmForProject = (project: Project) => {
  const uid = userStore.userInfo?.id
  if (!uid) return false
  if (project.created_by === uid) return true
  return (project.manager_user_ids ?? []).includes(uid)
}

const canEdit = (project: Project) => {
  if (userStore.hasRole('system_admin')) return true
  if (userStore.hasRole('project_manager')) {
    return isPmForProject(project)
  }
  return false
}

const canDelete = (project: Project) => {
  if (userStore.hasRole('system_admin')) return true
  if (userStore.hasRole('project_manager')) {
    return project.created_by === userStore.userInfo?.id
  }
  return false
}

const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadProjects = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }

    // 开发组长 / 管理员可按创建者筛选；项目经理不传 creator_id，由后端汇总「自建 + 协办」
    if (canViewAll.value && filterForm.creator_id) {
      params.creator_id = filterForm.creator_id
    }

    const result = await getProjects(params)
    
    // 客户端关键词筛选
    let filtered = result.items
    if (filterForm.keyword) {
      const keyword = filterForm.keyword.toLowerCase()
      filtered = filtered.filter(
        project =>
          project.name.toLowerCase().includes(keyword) ||
          (project.description && project.description.toLowerCase().includes(keyword))
      )
    }

    projectList.value = filtered
    pagination.total = result.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.keyword = ''
  filterForm.creator_id = undefined
  pagination.page = 1
  loadProjects()
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await createProject(createForm)
        ElMessage.success('项目创建成功')
        showCreateDialog.value = false
        loadProjects()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建项目失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    name: '',
    description: '',
    estimated_output_value: undefined,
  })
}

const showEditDialogFunc = async (project: Project) => {
  currentEditProject.value = project
  try {
    await loadPmCandidates()
    // 重新获取项目详情，确保数据最新
    const projectDetail = await getProject(project.id)
    Object.assign(editForm, {
      name: projectDetail.name,
      description: projectDetail.description || '',
      estimated_output_value: projectDetail.estimated_output_value
        ? Number(projectDetail.estimated_output_value)
        : undefined,
    })
    editManagerIds.value = projectDetail.manager_user_ids ? [...projectDetail.manager_user_ids] : []
    showEditDialogFlag.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载项目详情失败')
  }
}

const handleEdit = async () => {
  if (!editFormRef.value || !currentEditProject.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        const pid = currentEditProject.value!.id
        await updateProject(pid, editForm)
        if (canManageCoManagersInEdit.value) {
          await updateProjectManagers(pid, [...editManagerIds.value])
        }
        ElMessage.success('项目更新成功')
        showEditDialogFlag.value = false
        loadProjects()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '更新项目失败')
      } finally {
        editLoading.value = false
      }
    }
  })
}

const resetEditForm = () => {
  editFormRef.value?.resetFields()
  Object.assign(editForm, {
    name: '',
    description: '',
    estimated_output_value: undefined,
  })
  editManagerIds.value = []
  currentEditProject.value = null
}

const handleDelete = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${project.name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteProject(project.id)
    ElMessage.success('项目删除成功')
    loadProjects()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除项目失败')
    }
  }
}

const viewProject = (projectId: number) => {
  router.push({ name: 'ProjectDetail', params: { id: projectId } })
}

const viewProjectTasks = (projectId: number) => {
  router.push({ name: 'ProjectTaskExecution', params: { id: projectId } })
}

const viewProjectProgress = (projectId: number) => {
  router.push({ name: 'ProjectProgress', params: { id: projectId } })
}

const canViewTasks = (project: Project) => {
  if (userStore.hasAnyRole('system_admin', 'development_lead')) return true
  if (userStore.hasRole('project_manager')) {
    return isPmForProject(project)
  }
  return false
}

const showProjectDetail = async (projectId: number) => {
  try {
    const project = await getProject(projectId)
    await ElMessageBox.alert(
      `
      <div style="text-align: left; line-height: 2;">
        <p><strong>项目名称：</strong>${project.name}</p>
        <p><strong>项目描述：</strong>${project.description || '无'}</p>
        <p><strong>预计产值：</strong>${project.estimated_output_value ? formatMoney(project.estimated_output_value) : '未设置'}</p>
        <p><strong>创建时间：</strong>${formatDate(project.created_at)}</p>
      </div>
      `,
      '项目详情',
      { dangerouslyUseHTMLString: true }
    )
  } catch {
    // 用户点击关闭按钮，不做任何处理
  } finally {
    // 关闭弹窗后将 URL 归还至列表页，避免 URL 残留 id
    if (route.params.id) {
      router.replace({ name: 'ProjectList' })
    }
  }
}

const loadUsers = async () => {
  if (!canViewAll.value) return
  
  userLoading.value = true
  try {
    const result = await getUsers({ limit: 1000 })
    userList.value = result.items
  } catch (error) {
    // 忽略错误，不影响主功能
  } finally {
    userLoading.value = false
  }
}

// 监听路由参数：当 URL 为 /projects/:id 时自动弹出详情对话框
watch(
  () => route.params.id,
  (id) => {
    if (id) {
      showProjectDetail(Number(id))
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadProjects()
  loadUsers()
})
</script>

<style scoped>
.project-list-container {
  padding: 20px;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.project-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-placeholder {
  color: var(--el-text-color-placeholder);
}

.form-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
