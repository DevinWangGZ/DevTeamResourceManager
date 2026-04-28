<template>
  <div class="task-list-container">
    <Breadcrumb />
    <div class="task-header">
      <h2>任务管理</h2>
      <div class="header-actions">
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
        <el-button type="primary" @click="goToCreate">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" label-width="80px">
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.statuses"
            placeholder="全部"
            clearable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 220px"
          >
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
          <el-select
            v-model="filterForm.project_ids"
            placeholder="全部项目"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 220px"
            :loading="projectLoading"
          >
            <el-option
              v-for="proj in projectList"
              :key="proj.id"
              :label="proj.name"
              :value="proj.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="创建者">
          <el-select
            v-model="filterForm.creator_ids"
            placeholder="全部创建者"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 220px"
            :loading="userLoading"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.full_name ? `${user.full_name}（${user.username}）` : user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="认领者">
          <el-select
            v-model="filterForm.assignee_ids"
            placeholder="全部认领者"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 220px"
            :loading="userLoading"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.full_name ? `${user.full_name}（${user.username}）` : user.username"
              :value="user.id"
            />
          </el-select>
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
        <el-table-column prop="priority" label="优先级" width="110">
          <template #default="{ row }">
            <PriorityTag :priority="row.priority || 'P2'" :show-label="false" />
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewTask(row.id)">
              查看
            </el-button>
            <el-button
              v-if="canEdit(row)"
              link
              type="primary"
              size="small"
              @click="editTask(row.id)"
            >
              编辑
            </el-button>
            <el-button
              v-if="canPublish(row)"
              link
              type="success"
              size="small"
              @click="handlePublish(row.id)"
            >
              发布
            </el-button>
            <el-button
              v-if="canRevertToDraft(row)"
              link
              type="warning"
              size="small"
              @click="handleRevertToDraft(row.id)"
            >
              退回草稿
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
              v-if="canReturn(row)"
              link
              type="warning"
              size="small"
              @click="handleReturn(row)"
            >
              {{ isAssignee(row) ? '退回' : '收回' }}
            </el-button>
            <el-button
              v-if="canEvaluate(row)"
              link
              type="warning"
              size="small"
              @click="showEvaluateDialogFunc(row)"
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
              v-if="canRejectSubmitted(row)"
              link
              type="warning"
              size="small"
              @click="openRejectDialog(row)"
            >
              退回
            </el-button>
            <el-button
              v-if="canReopenConfirmed(row)"
              link
              type="warning"
              size="small"
              @click="handleReopen(row)"
            >
              重新打开
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
      <p
        v-if="collaboratorsAllocatedSumForSubmit > 0"
        style="margin: 0 0 12px; line-height: 1.5; color: var(--el-text-color-secondary); font-size: 13px"
      >
        配合人分配合计 <b style="color: var(--el-text-color-primary)">{{ collaboratorsAllocatedSumForSubmit }}</b>
        人天，实际投入人天须不少于该合计。
      </p>
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

    <!-- 退回已提交任务对话框 -->
    <el-dialog v-model="showRejectDialog" title="退回任务" width="520px" @close="resetRejectForm">
      <p style="color: var(--el-text-color-secondary); margin-bottom: 12px;">
        退回后任务将回到"进行中"状态，请填写退回原因以便认领人知悉。
      </p>
      <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
        <el-tag
          v-for="preset in rejectPresets"
          :key="preset"
          style="cursor: pointer;"
          @click="rejectForm.reason = preset"
        >
          {{ preset }}
        </el-tag>
      </div>
      <el-input
        v-model="rejectForm.reason"
        type="textarea"
        :rows="3"
        placeholder="请输入退回原因，或点击上方快捷选项"
        maxlength="500"
        show-word-limit
      />
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="warning" :loading="rejectLoading" @click="handleReject">
          确认退回
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import PriorityTag from '@/components/business/PriorityTag.vue'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Download } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getTasks,
  claimTask,
  evaluateTask,
  submitTask,
  confirmTask,
  deleteTask,
  publishTask,
  revertTaskToDraft,
  returnTask,
  rejectTask,
  reopenTask,
  getCollaborators,
  type Task,
} from '@/api/task'
import { exportTasks } from '@/api/export'
import { getProjects, type Project } from '@/api/project'
import { getUsers } from '@/api/user'
import type { UserInfo } from '@/api/auth'
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
  statuses: [] as string[],
  keyword: '',
  project_ids: [] as number[],
  creator_ids: [] as number[],
  assignee_ids: [] as number[],
  created_date_range: [] as string[],
  deadline_range: [] as string[],
  min_man_days: undefined as number | undefined,
  max_man_days: undefined as number | undefined,
  is_pinned: undefined as boolean | undefined,
})

const showEvaluateDialog = ref(false)
const currentEvaluateTask = ref<Task | null>(null)

const showSubmitDialog = ref(false)
const currentSubmitTask = ref<Task | null>(null)
const submitLoading = ref(false)

// 退回已提交任务
const showRejectDialog = ref(false)
const rejectLoading = ref(false)
const currentRejectTask = ref<Task | null>(null)
const rejectPresets = ['实际投入人天存在争议', '任务未达到预期']
const rejectForm = reactive({ reason: '' })

// 项目列表（用于筛选下拉）
const projectList = ref<Project[]>([])
const projectLoading = ref(false)

// 用户列表（用于创建者/认领者筛选下拉）
const userList = ref<UserInfo[]>([])
const userLoading = ref(false)

const submitFormRef = ref<FormInstance>()
const submitForm = reactive({
  actual_man_days: 0,
})

/** 列表页提交弹窗用：打开时拉取配合人分配合计 */
const collaboratorsAllocatedSumForSubmit = ref(0)

const submitActualManDaysListValidator = (
  _rule: unknown,
  value: number | undefined,
  callback: (error?: string | Error) => void
) => {
  const sum = collaboratorsAllocatedSumForSubmit.value
  if (sum > 0 && (value === undefined || value === null || Number(value) < sum)) {
    callback(new Error(`实际投入人天须不少于配合人分配合计（${sum} 人天）`))
  } else {
    callback()
  }
}

const submitRules: FormRules = {
  actual_man_days: [
    { required: true, message: '请输入实际投入人天', trigger: 'blur' },
    { validator: submitActualManDaysListValidator, trigger: 'blur' },
  ],
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
  return task.status === 'published' && userStore.hasRole('developer')
}

const canEvaluate = (task: Task) => {
  return (
    task.status === 'pending_eval' &&
    task.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
}

const canSubmit = (task: Task) => {
  return (
    (task.status === 'claimed' || task.status === 'in_progress') &&
    task.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
}

const canConfirm = (task: Task) => {
  return (
    task.status === 'submitted' &&
    (task.creator_id === userStore.userInfo?.id ||
      userStore.hasAnyRole('project_manager', 'system_admin'))
  )
}

// 已提交任务的退回权限：与确认权限相同（创建者 / PM / 管理员）
const canRejectSubmitted = (task: Task) => {
  return (
    task.status === 'submitted' &&
    (task.creator_id === userStore.userInfo?.id ||
      userStore.hasAnyRole('project_manager', 'system_admin'))
  )
}

const canReopenConfirmed = (task: Task) => {
  return (
    task.status === 'confirmed' &&
    (task.creator_id === userStore.userInfo?.id ||
      userStore.hasAnyRole('project_manager', 'system_admin'))
  )
}

const canDelete = (task: Task) => {
  return task.creator_id === userStore.userInfo?.id
}

// 草稿状态且是创建者或PM/管理员才可编辑
const canEdit = (task: Task) => {
  if (task.status !== 'draft') return false
  return (
    task.creator_id === userStore.userInfo?.id ||
    userStore.hasAnyRole('project_manager', 'system_admin')
  )
}

// 草稿状态且是创建者或PM/管理员才可发布
const canPublish = (task: Task) => {
  if (task.status !== 'draft') return false
  return (
    task.creator_id === userStore.userInfo?.id ||
    userStore.hasAnyRole('project_manager', 'system_admin')
  )
}

const isAssignee = (task: Task) => task.assignee_id === userStore.userInfo?.id

// 认领人可退回；创建者或PM/管理员可收回（已认领或进行中状态）
const canReturn = (task: Task) => {
  if (!['claimed', 'in_progress'].includes(task.status)) return false
  return (
    isAssignee(task) ||
    task.creator_id === userStore.userInfo?.id ||
    userStore.hasAnyRole('project_manager', 'system_admin')
  )
}

// 已发布状态且是创建者或PM/管理员才可退回草稿
const canRevertToDraft = (task: Task) => {
  if (task.status !== 'published') return false
  return (
    task.creator_id === userStore.userInfo?.id ||
    userStore.hasAnyRole('project_manager', 'system_admin')
  )
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    if (filterForm.statuses.length > 0) {
      params.statuses = filterForm.statuses.join(',')
    }
    if (filterForm.keyword) {
      params.keyword = filterForm.keyword
    }
    if (filterForm.project_ids.length > 0) {
      params.project_ids = filterForm.project_ids.join(',')
    }
    if (filterForm.creator_ids.length > 0) {
      params.creator_ids = filterForm.creator_ids.join(',')
    }
    if (filterForm.assignee_ids.length > 0) {
      params.assignee_ids = filterForm.assignee_ids.join(',')
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
  filterForm.statuses = []
  filterForm.keyword = ''
  filterForm.project_ids = []
  filterForm.creator_ids = []
  filterForm.assignee_ids = []
  filterForm.created_date_range = []
  filterForm.deadline_range = []
  filterForm.min_man_days = undefined
  filterForm.max_man_days = undefined
  filterForm.is_pinned = undefined
  showAdvancedFilter.value = false
  pagination.page = 1
  loadTasks()
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

const loadUsers = async () => {
  userLoading.value = true
  try {
    const result = await getUsers({ limit: 1000, is_active: true })
    userList.value = result.items
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    userLoading.value = false
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

const showSubmitDialogFunc = async (task: Task) => {
  currentSubmitTask.value = task
  collaboratorsAllocatedSumForSubmit.value = 0
  try {
    const list = await getCollaborators(task.id)
    collaboratorsAllocatedSumForSubmit.value = list.reduce(
      (s, c) => s + Number(c.allocated_man_days),
      0
    )
  } catch {
    collaboratorsAllocatedSumForSubmit.value = 0
  }
  const est = Number(task.estimated_man_days || 0)
  const sum = collaboratorsAllocatedSumForSubmit.value
  submitForm.actual_man_days = Math.max(est, sum) || est || 0.01
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
  collaboratorsAllocatedSumForSubmit.value = 0
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

const openRejectDialog = (task: Task) => {
  currentRejectTask.value = task
  rejectForm.reason = ''
  showRejectDialog.value = true
}

const resetRejectForm = () => {
  rejectForm.reason = ''
  currentRejectTask.value = null
}

const handleReject = async () => {
  if (!currentRejectTask.value) return
  if (!rejectForm.reason.trim()) {
    ElMessage.warning('请填写退回原因')
    return
  }
  rejectLoading.value = true
  try {
    await rejectTask(currentRejectTask.value.id, rejectForm.reason.trim())
    ElMessage.success('任务已退回，认领人可重新修改后提交')
    showRejectDialog.value = false
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '退回任务失败')
  } finally {
    rejectLoading.value = false
  }
}

const handleReopen = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定重新打开任务"${task.title}"吗？重新打开后任务状态将回到“进行中”，相关确认统计会回滚。`,
      '重新打开任务',
      {
        confirmButtonText: '确定重新打开',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await reopenTask(task.id)
    ElMessage.success('任务已重新打开')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重新打开任务失败')
    }
  }
}

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

const editTask = (taskId: number) => {
  router.push({ name: 'TaskEdit', params: { id: taskId } })
}

const handleReturn = async (task: Task) => {
  const isMe = isAssignee(task)
  const label = isMe ? '退回' : '收回'
  try {
    await ElMessageBox.confirm(
      isMe
        ? '确定要退回此任务吗？任务将重新回到"已发布"状态，可被其他人认领。'
        : `确定要收回任务"${task.title}"吗？任务将重新回到"已发布"状态，认领人和排期信息将被清除。`,
      `${label}任务`,
      { confirmButtonText: `确定${label}`, cancelButtonText: '取消', type: 'warning' }
    )
    await returnTask(task.id)
    ElMessage.success(`任务已${label}`)
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || `${label}失败`)
    }
  }
}

const handleRevertToDraft = async (taskId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要将此任务退回草稿状态吗？退回后任务将从任务集市下架，需重新发布才能认领。',
      '退回草稿确认',
      {
        confirmButtonText: '确定退回',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await revertTaskToDraft(taskId)
    ElMessage.success('任务已退回草稿')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '退回草稿失败')
    }
  }
}

const handlePublish = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要发布此任务吗？发布后开发者将可以认领该任务。', '发布确认', {
      confirmButtonText: '确定发布',
      cancelButtonText: '取消',
      type: 'info',
    })
    await publishTask(taskId)
    ElMessage.success('任务发布成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '发布任务失败')
    }
  }
}

const goToCreate = () => {
  router.push({ name: 'TaskCreate' })
}

const handleExport = async () => {
  try {
    const params: any = {}
    if (filterForm.statuses.length > 0) {
      params.statuses = filterForm.statuses.join(',')
    }
    if (filterForm.project_ids.length > 0) {
      params.project_ids = filterForm.project_ids.join(',')
    }
    if (filterForm.creator_ids.length > 0) {
      params.creator_ids = filterForm.creator_ids.join(',')
    }
    if (filterForm.assignee_ids.length > 0) {
      params.assignee_ids = filterForm.assignee_ids.join(',')
    }
    if (filterForm.keyword) {
      params.keyword = filterForm.keyword
    }

    const blob = await exportTasks(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `任务列表_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导出失败')
  }
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
  loadUsers()
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

.task-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
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
