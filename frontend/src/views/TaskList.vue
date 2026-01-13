<template>
  <div class="task-list-container">
    <Breadcrumb />
    <div class="task-header">
      <h2>任务管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" label-width="80px">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 150px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="待评估" value="pending_eval" />
            <el-option label="已认领" value="claimed" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-input-number
            v-model="filterForm.project_id"
            placeholder="项目ID"
            clearable
            style="width: 150px"
            :min="1"
          />
        </el-form-item>
        <el-form-item label="创建者">
          <el-input-number
            v-model="filterForm.creator_id"
            placeholder="创建者ID"
            clearable
            style="width: 150px"
            :min="1"
          />
        </el-form-item>
        <el-form-item label="认领者">
          <el-input-number
            v-model="filterForm.assignee_id"
            placeholder="认领者ID"
            clearable
            style="width: 150px"
            :min="1"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索任务标题或描述"
            clearable
            style="width: 200px"
            @keyup.enter="loadTasks"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks" :icon="Search">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
          <el-button link type="primary" @click="showAdvancedFilter = !showAdvancedFilter">
            {{ showAdvancedFilter ? '收起' : '展开' }}高级筛选
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 高级筛选 -->
      <el-collapse-transition>
        <div v-show="showAdvancedFilter" class="advanced-filter">
          <el-divider />
          <el-form :inline="true" :model="filterForm" label-width="100px">
            <el-form-item label="创建时间">
              <el-date-picker
                v-model="filterForm.created_date_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 240px"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="截止时间">
              <el-date-picker
                v-model="filterForm.deadline_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 240px"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="投入人天">
              <el-input-number
                v-model="filterForm.min_man_days"
                placeholder="最小"
                :min="0"
                :precision="2"
                style="width: 120px"
              />
              <span style="margin: 0 10px">-</span>
              <el-input-number
                v-model="filterForm.max_man_days"
                placeholder="最大"
                :min="0"
                :precision="2"
                style="width: 120px"
              />
            </el-form-item>
            <el-form-item label="置顶状态">
              <el-select v-model="filterForm.is_pinned" placeholder="全部" clearable style="width: 120px">
                <el-option label="已置顶" :value="true" />
                <el-option label="未置顶" :value="false" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="task-card">
      <el-table :data="taskList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="任务标题" min-width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_man_days" label="拟投入人天" width="120" />
        <el-table-column prop="actual_man_days" label="实际投入人天" width="120" />
        <el-table-column prop="creator_name" label="创建者" width="120" />
        <el-table-column prop="assignee_name" label="认领者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewTask(row.id)">
              查看
            </el-button>
            <el-button
              v-if="canClaim(row)"
              link
              type="success"
              size="small"
              @click="handleClaim(row.id)"
            >
              认领
            </el-button>
            <el-button
              v-if="canEvaluate(row)"
              link
              type="warning"
              size="small"
              @click="showEvaluateDialog(row)"
            >
              评估
            </el-button>
            <el-button
              v-if="canSubmit(row)"
              link
              type="primary"
              size="small"
              @click="showSubmitDialogFunc(row)"
            >
              提交
            </el-button>
            <el-button
              v-if="canConfirm(row)"
              link
              type="success"
              size="small"
              @click="handleConfirm(row.id)"
            >
              确认
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
          @size-change="loadTasks"
          @current-change="loadTasks"
        />
      </div>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建任务"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="createForm.project_id"
            placeholder="请选择项目"
            filterable
            style="width: 100%"
            clearable
            :loading="projectLoading"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        <el-form-item label="拟投入人天" prop="estimated_man_days">
          <el-input-number
            v-model="createForm.estimated_man_days"
            :min="0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="所需技能" prop="required_skills">
          <el-input
            v-model="createForm.required_skills"
            placeholder="请输入所需技能（逗号分隔）"
          />
        </el-form-item>
        <el-form-item label="截止时间" prop="deadline">
          <el-date-picker
            v-model="createForm.deadline"
            type="date"
            placeholder="选择截止时间"
            style="width: 100%"
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

    <!-- 评估任务对话框 -->
    <el-dialog v-model="showEvaluateDialog" title="评估任务" width="500px">
      <p>是否接受此任务？</p>
      <template #footer>
        <el-button @click="showEvaluateDialog = false">取消</el-button>
        <el-button type="danger" @click="handleEvaluate(false)">拒绝</el-button>
        <el-button type="primary" @click="handleEvaluate(true)">接受</el-button>
      </template>
    </el-dialog>

    <!-- 提交任务对话框 -->
    <el-dialog
      v-model="showSubmitDialog"
      title="提交任务"
      width="500px"
      @close="resetSubmitForm"
    >
      <el-form ref="submitFormRef" :model="submitForm" :rules="submitRules" label-width="100px">
        <el-form-item label="实际投入人天" prop="actual_man_days">
          <el-input-number
            v-model="submitForm.actual_man_days"
            :min="0.01"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getTasks,
  createTask,
  claimTask,
  evaluateTask,
  submitTask,
  confirmTask,
  deleteTask,
  type Task,
  type TaskCreate,
} from '@/api/task'
import { getProjects, type Project } from '@/api/project'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const taskList = ref<Task[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const showAdvancedFilter = ref(false)
const filterForm = reactive({
  status: '',
  keyword: '',
  project_id: undefined as number | undefined,
  creator_id: undefined as number | undefined,
  assignee_id: undefined as number | undefined,
  created_date_range: [] as string[],
  deadline_range: [] as string[],
  min_man_days: undefined as number | undefined,
  max_man_days: undefined as number | undefined,
  is_pinned: undefined as boolean | undefined,
})

const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<TaskCreate>({
  title: '',
  description: '',
  project_id: undefined,
  estimated_man_days: 0,
  required_skills: '',
})

const showEvaluateDialog = ref(false)
const currentEvaluateTask = ref<Task | null>(null)

const showSubmitDialog = ref(false)
const currentSubmitTask = ref<Task | null>(null)
const submitLoading = ref(false)

// 项目列表
const projectList = ref<Project[]>([])
const projectLoading = ref(false)
const submitFormRef = ref<FormInstance>()
const submitForm = reactive({
  actual_man_days: 0,
})

const createRules: FormRules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  estimated_man_days: [{ required: true, message: '请输入拟投入人天', trigger: 'blur' }],
}

const submitRules: FormRules = {
  actual_man_days: [{ required: true, message: '请输入实际投入人天', trigger: 'blur' }],
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    pending_eval: '待评估',
    claimed: '已认领',
    in_progress: '进行中',
    submitted: '已提交',
    confirmed: '已确认',
    archived: '已归档',
  }
  return statusMap[status] || status
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    published: 'success',
    pending_eval: 'warning',
    claimed: '',
    in_progress: 'primary',
    submitted: 'warning',
    confirmed: 'success',
    archived: 'info',
  }
  return typeMap[status] || ''
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const canClaim = (task: Task) => {
  return task.status === 'published' && userStore.userInfo?.role === 'developer'
}

const canEvaluate = (task: Task) => {
  return (
    task.status === 'pending_eval' &&
    task.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
  )
}

const canSubmit = (task: Task) => {
  return (
    (task.status === 'claimed' || task.status === 'in_progress') &&
    task.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
  )
}

const canConfirm = (task: Task) => {
  return (
    task.status === 'submitted' &&
    (userStore.userInfo?.role === 'project_manager' ||
      userStore.userInfo?.role === 'system_admin')
  )
}

const canDelete = (task: Task) => {
  // 只有创建者可以删除自己创建的任务
  return task.creator_id === userStore.userInfo?.id
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    if (filterForm.status) {
      params.status = filterForm.status
    }
    if (filterForm.keyword) {
      params.keyword = filterForm.keyword
    }
    if (filterForm.project_id) {
      params.project_id = filterForm.project_id
    }
    if (filterForm.creator_id) {
      params.creator_id = filterForm.creator_id
    }
    if (filterForm.assignee_id) {
      params.assignee_id = filterForm.assignee_id
    }

    const result = await getTasks(params)
    taskList.value = result.items
    pagination.total = result.total

    // 客户端筛选（高级筛选）
    if (showAdvancedFilter.value) {
      let filtered = result.items

      // 置顶状态筛选
      if (filterForm.is_pinned !== undefined) {
        filtered = filtered.filter(task => task.is_pinned === filterForm.is_pinned)
      }

      // 投入人天筛选
      if (filterForm.min_man_days !== undefined) {
        filtered = filtered.filter(task => task.estimated_man_days >= filterForm.min_man_days!)
      }
      if (filterForm.max_man_days !== undefined) {
        filtered = filtered.filter(task => task.estimated_man_days <= filterForm.max_man_days!)
      }

      // 创建时间筛选
      if (filterForm.created_date_range && filterForm.created_date_range.length === 2) {
        const [start, end] = filterForm.created_date_range
        filtered = filtered.filter(task => {
          const created = new Date(task.created_at).toISOString().split('T')[0]
          return created >= start && created <= end
        })
      }

      // 截止时间筛选
      if (filterForm.deadline_range && filterForm.deadline_range.length === 2) {
        const [start, end] = filterForm.deadline_range
        filtered = filtered.filter(task => {
          if (!task.deadline) return false
          const deadline = task.deadline
          return deadline >= start && deadline <= end
        })
      }

      taskList.value = filtered
    }
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.keyword = ''
  filterForm.project_id = undefined
  filterForm.creator_id = undefined
  filterForm.assignee_id = undefined
  filterForm.created_date_range = []
  filterForm.deadline_range = []
  filterForm.min_man_days = undefined
  filterForm.max_man_days = undefined
  filterForm.is_pinned = undefined
  showAdvancedFilter.value = false
  pagination.page = 1
  loadTasks()
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await createTask(createForm)
        ElMessage.success('任务创建成功')
        showCreateDialog.value = false
        loadTasks()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建任务失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    title: '',
    description: '',
    project_id: undefined,
    estimated_man_days: 0,
    required_skills: '',
    deadline: undefined,
  })
}

const loadProjects = async () => {
  projectLoading.value = true
  try {
    const result = await getProjects({ limit: 1000 })
    projectList.value = result.items
  } catch (error) {
    ElMessage.error('加载项目列表失败')
  } finally {
    projectLoading.value = false
  }
}

const handleClaim = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要认领此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await claimTask(taskId)
    ElMessage.success('任务认领成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '认领任务失败')
    }
  }
}

const showEvaluateDialogFunc = (task: Task) => {
  currentEvaluateTask.value = task
  showEvaluateDialog.value = true
}

const handleEvaluate = async (accept: boolean) => {
  if (!currentEvaluateTask.value) return

  try {
    await evaluateTask(currentEvaluateTask.value.id, { accept })
    ElMessage.success(accept ? '任务已接受' : '任务已拒绝')
    showEvaluateDialog.value = false
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const showSubmitDialogFunc = (task: Task) => {
  currentSubmitTask.value = task
  submitForm.actual_man_days = task.estimated_man_days || 0
  showSubmitDialog.value = true
}

const handleSubmit = async () => {
  if (!submitFormRef.value || !currentSubmitTask.value) return

  await submitFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await submitTask(currentSubmitTask.value!.id, {
          actual_man_days: submitForm.actual_man_days,
        })
        ElMessage.success('任务提交成功')
        showSubmitDialog.value = false
        loadTasks()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '提交任务失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const resetSubmitForm = () => {
  submitFormRef.value?.resetFields()
  submitForm.actual_man_days = 0
  currentSubmitTask.value = null
}

const handleConfirm = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要确认此任务已完成吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await confirmTask(taskId)
    ElMessage.success('任务确认成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '确认任务失败')
    }
  }
}

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

const handleDelete = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务"${task.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteTask(task.id)
    ElMessage.success('任务删除成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除任务失败')
    }
  }
}

onMounted(() => {
  loadTasks()
  loadProjects()
})
</script>

<style scoped>
.task-list-container {
  padding: 20px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.task-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
