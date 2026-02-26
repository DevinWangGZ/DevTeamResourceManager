<template>
  <div class="task-detail-container">
    <Breadcrumb />
    <el-card v-loading="loading">
      <template #header>
        <div class="task-header">
          <div class="task-title">
            <el-icon v-if="task?.is_pinned" class="pin-icon"><StarFilled /></el-icon>
            <h2>{{ task?.title || '加载中...' }}</h2>
            <el-tag :type="getStatusType(task?.status)" class="status-tag">
              {{ getStatusText(task?.status) }}
            </el-tag>
          </div>
          <div class="task-actions">
            <el-button @click="goBack">返回</el-button>
            <el-button
              v-if="canPublish"
              type="primary"
              @click="handlePublish"
            >
              发布
            </el-button>
            <el-button
              v-if="canClaim"
              type="success"
              @click="handleClaim"
            >
              认领
            </el-button>
            <el-button
              v-if="canEvaluate"
              type="warning"
              @click="showEvaluateDialog = true"
            >
              评估
            </el-button>
            <el-button
              v-if="canStart"
              type="primary"
              @click="handleStart"
            >
              开始
            </el-button>
            <el-button
              v-if="canReturn"
              type="warning"
              @click="handleReturn"
            >
              {{ isCurrentUserAssignee ? '退回任务' : '收回任务' }}
            </el-button>
            <el-button
              v-if="canSubmit"
              type="primary"
              @click="openSubmitDialog"
            >
              提交
            </el-button>
            <el-button
              v-if="canConfirm"
              type="success"
              @click="handleConfirm"
            >
              确认
            </el-button>
            <el-button
              v-if="canRejectSubmitted"
              type="warning"
              @click="showRejectDialogDetail = true"
            >
              退回
            </el-button>
            <el-button
              v-if="canPin"
              :type="task?.is_pinned ? 'warning' : 'default'"
              @click="handlePin"
            >
              {{ task?.is_pinned ? '取消置顶' : '置顶' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="task-content" v-if="task">
        <!-- 基本信息 -->
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">{{ task.creator_name || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="认领者">{{ task.assignee_name || '未认领' }}</el-descriptions-item>
          <el-descriptions-item label="项目">{{ task.project_name || '未关联项目' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(task.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="拟投入人天">{{ task.estimated_man_days }} 人天</el-descriptions-item>
          <el-descriptions-item label="实际投入人天">
            <span v-if="task.actual_man_days">{{ task.actual_man_days }} 人天</span>
            <span v-else class="text-muted">未填写</span>
          </el-descriptions-item>
          <el-descriptions-item label="截止时间" :span="2">
            <span v-if="task.deadline">{{ formatDate(task.deadline) }}</span>
            <span v-else class="text-muted">未设置</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="task.rejection_reason" label="退回原因" :span="2">
            <el-tag type="warning" style="white-space: normal; height: auto; padding: 4px 8px;">
              {{ task.rejection_reason }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 任务描述 -->
        <el-card class="description-card" shadow="never">
          <template #header>
            <span>任务描述</span>
          </template>
          <div class="description-content">
            <MarkdownViewer v-if="task.description" :content="task.description" />
            <p v-else class="text-muted">暂无描述</p>
          </div>
        </el-card>

        <!-- 所需技能 -->
        <el-card class="skills-card" shadow="never" v-if="task.required_skills">
          <template #header>
            <span>所需技能</span>
          </template>
          <div class="skills-content">
            <el-tag
              v-for="(skill, index) in getSkillsList(task.required_skills)"
              :key="index"
              class="skill-tag"
            >
              {{ skill }}
            </el-tag>
          </div>
        </el-card>

        <!-- 排期信息 -->
        <el-card class="schedule-card" shadow="never" v-if="schedule">
          <template #header>
            <span>排期信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="预计开始时间">
              {{ formatDate(schedule.start_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="预计结束时间">
              {{ formatDate(schedule.end_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="预计工作日">
              {{ schedule.work_days }} 天
            </el-descriptions-item>
            <el-descriptions-item label="置顶状态">
              <el-tag :type="schedule.is_pinned ? 'warning' : 'info'">
                {{ schedule.is_pinned ? '已置顶' : '未置顶' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 任务配合人 -->
        <el-card
          class="collaborators-card"
          shadow="never"
          v-if="task.assignee_id"
        >
          <template #header>
            <div class="collaborators-header">
              <span>任务配合人</span>
              <div class="collaborators-header-right">
                <span class="man-days-summary">
                  已分配 <b>{{ collaboratorsTotalDays }}</b> / 拟投入 <b>{{ task.estimated_man_days }}</b> 人天
                </span>
                <el-button
                  v-if="canManageCollaborators"
                  type="primary"
                  size="small"
                  @click="openAddCollaboratorDialog"
                >
                  + 添加配合人
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="collaborators.length === 0" class="collaborators-empty">
            <el-empty description="暂无配合人" :image-size="60" />
          </div>
          <el-table v-else :data="collaborators" size="small">
            <el-table-column label="配合人" min-width="120">
              <template #default="{ row }">
                <span>{{ row.user_full_name || row.user_name }}</span>
                <el-tag size="small" type="info" style="margin-left: 6px">{{ row.user_name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="分配人天" width="120">
              <template #default="{ row }">
                {{ row.allocated_man_days }} 人天
              </template>
            </el-table-column>
            <el-table-column v-if="canManageCollaborators" label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="openEditCollaborator(row)"
                >
                  调整人天
                </el-button>
                <el-button
                  link
                  type="danger"
                  size="small"
                  @click="handleRemoveCollaborator(row)"
                >
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-card>

    <!-- 添加配合人对话框 -->
    <el-dialog v-model="showAddCollaboratorDialog" title="添加配合人" width="480px" @close="resetAddForm">
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="100px">
        <el-form-item label="选择配合人" prop="user_id">
          <el-select
            v-model="addForm.user_id"
            filterable
            placeholder="搜索姓名或用户名"
            style="width: 100%"
            :loading="developerListLoading"
            no-match-text="未找到匹配的开发人员"
            no-data-text="暂无开发人员数据"
          >
            <el-option
              v-for="dev in availableDevelopers"
              :key="dev.id"
              :label="dev.full_name ? `${dev.full_name}（${dev.username}）` : dev.username"
              :value="dev.id"
            >
              <div class="developer-option">
                <span class="dev-name">{{ dev.full_name || dev.username }}</span>
                <span class="dev-username">@{{ dev.username }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="分配人天" prop="allocated_man_days">
          <el-input-number
            v-model="addForm.allocated_man_days"
            :min="0.01"
            :max="remainingManDays || 0.01"
            :precision="2"
            style="width: 100%"
          />
          <div class="form-hint">
            剩余可分配：<b>{{ remainingManDays }}</b> 人天
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCollaboratorDialog = false">取消</el-button>
        <el-button type="primary" :loading="collaboratorLoading" @click="handleAddCollaborator">
          确认添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑配合人人天对话框 -->
    <el-dialog v-model="showEditCollaboratorDialog" title="调整分配人天" width="440px">
      <el-form label-width="100px">
        <el-form-item label="配合人">
          <span>{{ editCollaborator?.user_full_name || editCollaborator?.user_name }}</span>
        </el-form-item>
        <el-form-item label="分配人天">
          <el-input-number
            v-model="editManDays"
            :min="0.01"
            :precision="2"
            style="width: 100%"
          />
          <div class="form-hint">
            剩余可分配（不含本条）：{{ remainingManDaysForEdit }} 人天
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditCollaboratorDialog = false">取消</el-button>
        <el-button type="primary" :loading="collaboratorLoading" @click="handleUpdateCollaborator">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 评估对话框 -->
    <el-dialog v-model="showEvaluateDialog" title="评估任务" width="500px">
      <p>是否接受此任务？</p>
      <template #footer>
        <el-button @click="showEvaluateDialog = false">取消</el-button>
        <el-button type="danger" @click="handleEvaluate(false)">拒绝</el-button>
        <el-button type="primary" @click="handleEvaluate(true)">接受</el-button>
      </template>
    </el-dialog>

    <!-- 提交对话框 -->
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

    <!-- 退回已提交任务对话框 -->
    <el-dialog
      v-model="showRejectDialogDetail"
      title="退回任务"
      width="520px"
      @close="rejectReasonDetail = ''"
    >
      <p style="color: var(--el-text-color-secondary); margin-bottom: 12px;">
        退回后任务将回到"进行中"状态，请填写退回原因以便认领人知悉。
      </p>
      <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
        <el-tag
          v-for="preset in rejectPresetsDetail"
          :key="preset"
          style="cursor: pointer;"
          @click="rejectReasonDetail = preset"
        >
          {{ preset }}
        </el-tag>
      </div>
      <el-input
        v-model="rejectReasonDetail"
        type="textarea"
        :rows="3"
        placeholder="请输入退回原因，或点击上方快捷选项"
        maxlength="500"
        show-word-limit
      />
      <template #footer>
        <el-button @click="showRejectDialogDetail = false">取消</el-button>
        <el-button type="warning" :loading="rejectLoadingDetail" @click="handleRejectDetail">
          确认退回
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import MarkdownViewer from '@/components/ui/MarkdownViewer.vue'
import { ref, reactive, computed, onMounted, type FormInstance, type FormRules } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getTask,
  publishTask,
  claimTask,
  evaluateTask,
  startTask,
  submitTask,
  confirmTask,
  rejectTask,
  pinTask,
  getTaskSchedule,
  getCollaborators,
  addCollaborator,
  updateCollaborator,
  removeCollaborator,
  returnTask,
  type TaskDetail,
  type Collaborator,
} from '@/api/task'
import { getDevelopers } from '@/api/user'
import type { UserInfo } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const task = ref<TaskDetail | null>(null)
const schedule = ref<any>(null)

const showEvaluateDialog = ref(false)
const showSubmitDialog = ref(false)
const submitLoading = ref(false)
const submitFormRef = ref<FormInstance>()
const submitForm = reactive({
  actual_man_days: 0,
})

// 退回已提交任务
const showRejectDialogDetail = ref(false)
const rejectLoadingDetail = ref(false)
const rejectReasonDetail = ref('')
const rejectPresetsDetail = ['实际投入人天存在争议', '任务未达到预期']

const submitRules: FormRules = {
  actual_man_days: [{ required: true, message: '请输入实际投入人天', trigger: 'blur' }],
}

// ---- 配合人 ----
const collaborators = ref<Collaborator[]>([])
const collaboratorLoading = ref(false)
const showAddCollaboratorDialog = ref(false)
const showEditCollaboratorDialog = ref(false)
const editCollaborator = ref<Collaborator | null>(null)
const editManDays = ref(0)
const addFormRef = ref<FormInstance>()
const addForm = reactive({ user_id: undefined as number | undefined, allocated_man_days: 1 })
const addFormRules: FormRules = {
  user_id: [{ required: true, message: '请选择配合人', trigger: 'change' }],
  allocated_man_days: [{ required: true, message: '请输入分配人天', trigger: 'blur' }],
}

// 开发人员列表（用于下拉搜索）
const developerList = ref<UserInfo[]>([])
const developerListLoading = ref(false)

// 过滤掉认领人和已添加的配合人
const availableDevelopers = computed(() => {
  const excludeIds = new Set<number>()
  if (task.value?.assignee_id) excludeIds.add(task.value.assignee_id)
  collaborators.value.forEach(c => excludeIds.add(c.user_id))
  return developerList.value.filter(d => !excludeIds.has(d.id))
})

const loadDeveloperList = async () => {
  developerListLoading.value = true
  try {
    const res = await getDevelopers()
    developerList.value = res.items
  } catch {
    // 加载失败不阻断流程
  } finally {
    developerListLoading.value = false
  }
}

const collaboratorsTotalDays = computed(() =>
  collaborators.value.reduce((sum, c) => sum + Number(c.allocated_man_days), 0)
)

const remainingManDays = computed(() => {
  const total = Number(task.value?.estimated_man_days || 0)
  return Math.max(0, total - collaboratorsTotalDays.value)
})

const remainingManDaysForEdit = computed(() => {
  if (!editCollaborator.value) return 0
  const total = Number(task.value?.estimated_man_days || 0)
  const others = collaborators.value
    .filter(c => c.user_id !== editCollaborator.value!.user_id)
    .reduce((sum, c) => sum + Number(c.allocated_man_days), 0)
  return Math.max(0, total - others)
})

const canManageCollaborators = computed(() => {
  if (!task.value || !userStore.userInfo) return false
  const activeStatuses = ['claimed', 'in_progress']
  return (
    activeStatuses.includes(task.value.status) &&
    task.value.assignee_id === userStore.userInfo.id
  )
})

const getStatusText = (status?: string) => {
  if (!status) return ''
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

const getStatusType = (status?: string) => {
  if (!status) return 'info'
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

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getSkillsList = (skills?: string) => {
  if (!skills) return []
  return skills.split(',').map(s => s.trim()).filter(s => s)
}

const canPublish = computed(() => {
  if (!task.value || !userStore.userInfo) return false
  const isCreator = task.value.creator_id === userStore.userInfo.id
  const isManager = userStore.hasAnyRole('project_manager', 'system_admin')
  const isDraft = task.value.status === 'draft'
  return isDraft && isCreator && isManager
})

const canClaim = computed(() => {
  return (
    task.value?.status === 'published' &&
    userStore.hasRole('developer')
  )
})

const canEvaluate = computed(() => {
  return (
    task.value?.status === 'pending_eval' &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
})

const canStart = computed(() => {
  return (
    task.value?.status === 'claimed' &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
})

const canSubmit = computed(() => {
  return (
    (task.value?.status === 'claimed' || task.value?.status === 'in_progress') &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
})

const canConfirm = computed(() => {
  return (
    task.value?.status === 'submitted' &&
    (task.value?.creator_id === userStore.userInfo?.id ||
      userStore.hasAnyRole('project_manager', 'system_admin'))
  )
})

// 已提交任务退回权限（与确认相同）
const canRejectSubmitted = computed(() => {
  return (
    task.value?.status === 'submitted' &&
    (task.value?.creator_id === userStore.userInfo?.id ||
      userStore.hasAnyRole('project_manager', 'system_admin'))
  )
})

const isCurrentUserAssignee = computed(
  () => task.value?.assignee_id === userStore.userInfo?.id
)

const canReturn = computed(() => {
  if (!task.value || !userStore.userInfo) return false
  if (!['claimed', 'in_progress'].includes(task.value.status)) return false
  return (
    isCurrentUserAssignee.value ||
    task.value.creator_id === userStore.userInfo.id ||
    userStore.hasAnyRole('project_manager', 'system_admin')
  )
})

const canPin = computed(() => {
  return (
    (task.value?.status === 'claimed' || task.value?.status === 'in_progress') &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.hasRole('developer')
  )
})

const loadTask = async () => {
  const taskId = Number(route.params.id)
  if (!taskId) {
    ElMessage.error('任务ID无效')
    router.push('/tasks')
    return
  }

  loading.value = true
  try {
    task.value = await getTask(taskId)
    if (task.value.assignee_id) {
      try { schedule.value = await getTaskSchedule(taskId) } catch {}
      try { collaborators.value = await getCollaborators(taskId) } catch {}
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载任务详情失败')
    router.push('/tasks')
  } finally {
    loading.value = false
  }
}

const loadCollaborators = async () => {
  if (!task.value) return
  try {
    collaborators.value = await getCollaborators(task.value.id)
  } catch {}
}

const openAddCollaboratorDialog = async () => {
  await loadDeveloperList()
  showAddCollaboratorDialog.value = true
}

const resetAddForm = () => {
  addFormRef.value?.resetFields()
  addForm.user_id = undefined
  addForm.allocated_man_days = 1
}

const handleAddCollaborator = async () => {
  if (!addFormRef.value || !task.value) return
  await addFormRef.value.validate(async (valid) => {
    if (!valid) return
    collaboratorLoading.value = true
    try {
      await addCollaborator(task.value!.id, {
        user_id: addForm.user_id!,
        allocated_man_days: addForm.allocated_man_days,
      })
      ElMessage.success('配合人添加成功')
      showAddCollaboratorDialog.value = false
      await loadCollaborators()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '添加配合人失败')
    } finally {
      collaboratorLoading.value = false
    }
  })
}

const openEditCollaborator = (row: Collaborator) => {
  editCollaborator.value = row
  editManDays.value = Number(row.allocated_man_days)
  showEditCollaboratorDialog.value = true
}

const handleUpdateCollaborator = async () => {
  if (!task.value || !editCollaborator.value) return
  collaboratorLoading.value = true
  try {
    await updateCollaborator(task.value.id, editCollaborator.value.user_id, {
      allocated_man_days: editManDays.value,
    })
    ElMessage.success('人天调整成功')
    showEditCollaboratorDialog.value = false
    await loadCollaborators()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    collaboratorLoading.value = false
  }
}

const handleRemoveCollaborator = async (row: Collaborator) => {
  if (!task.value) return
  try {
    await ElMessageBox.confirm(
      `确定移除配合人「${row.user_full_name || row.user_name}」吗？`,
      '移除配合人',
      { confirmButtonText: '确定移除', cancelButtonText: '取消', type: 'warning' }
    )
    await removeCollaborator(task.value.id, row.user_id)
    ElMessage.success('配合人已移除')
    await loadCollaborators()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '移除失败')
    }
  }
}

const goBack = () => {
  router.push('/tasks')
}

const handlePublish = async () => {
  if (!task.value) return
  try {
    await ElMessageBox.confirm('确定要发布此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await publishTask(task.value.id)
    ElMessage.success('任务发布成功')
    loadTask()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '发布任务失败')
    }
  }
}

const handleClaim = async () => {
  if (!task.value) return
  try {
    await ElMessageBox.confirm('确定要认领此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await claimTask(task.value.id)
    ElMessage.success('任务认领成功')
    loadTask()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '认领任务失败')
    }
  }
}

const handleEvaluate = async (accept: boolean) => {
  if (!task.value) return
  try {
    await evaluateTask(task.value.id, { accept })
    ElMessage.success(accept ? '任务已接受' : '任务已拒绝')
    showEvaluateDialog.value = false
    loadTask()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleStart = async () => {
  if (!task.value) return
  try {
    await startTask(task.value.id)
    ElMessage.success('任务已开始')
    loadTask()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '开始任务失败')
  }
}

const handleSubmit = async () => {
  if (!submitFormRef.value || !task.value) return

  await submitFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await submitTask(task.value!.id, {
          actual_man_days: submitForm.actual_man_days,
        })
        ElMessage.success('任务提交成功')
        showSubmitDialog.value = false
        loadTask()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '提交任务失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const openSubmitDialog = () => {
  submitForm.actual_man_days = task.value?.estimated_man_days || 0
  showSubmitDialog.value = true
}

const resetSubmitForm = () => {
  submitFormRef.value?.resetFields()
  submitForm.actual_man_days = task.value?.estimated_man_days || 0
}

const handleConfirm = async () => {
  if (!task.value) return
  try {
    await ElMessageBox.confirm('确定要确认此任务已完成吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await confirmTask(task.value.id)
    ElMessage.success('任务确认成功')
    loadTask()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '确认任务失败')
    }
  }
}

const handleRejectDetail = async () => {
  if (!task.value) return
  if (!rejectReasonDetail.value.trim()) {
    ElMessage.warning('请填写退回原因')
    return
  }
  rejectLoadingDetail.value = true
  try {
    await rejectTask(task.value.id, rejectReasonDetail.value.trim())
    ElMessage.success('任务已退回，认领人可重新修改后提交')
    showRejectDialogDetail.value = false
    rejectReasonDetail.value = ''
    loadTask()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '退回任务失败')
  } finally {
    rejectLoadingDetail.value = false
  }
}

const handleReturn = async () => {
  if (!task.value) return
  const isMe = isCurrentUserAssignee.value
  const label = isMe ? '退回' : '收回'
  try {
    await ElMessageBox.confirm(
      isMe
        ? '确定要退回此任务吗？任务将重新回到"已发布"状态，可被其他人认领。'
        : '确定要收回此任务吗？任务将重新回到"已发布"状态，认领人和排期信息将被清除。',
      `${label}任务`,
      { confirmButtonText: `确定${label}`, cancelButtonText: '取消', type: 'warning' }
    )
    await returnTask(task.value.id)
    ElMessage.success(`任务已${label}`)
    loadTask()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || `${label}失败`)
    }
  }
}

const handlePin = async () => {
  if (!task.value) return
  try {
    const isPinned = !task.value.is_pinned
    await pinTask(task.value.id, { is_pinned: isPinned })
    ElMessage.success(isPinned ? '任务已置顶' : '任务已取消置顶')
    loadTask()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

onMounted(() => {
  loadTask()
})
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-title h2 {
  margin: 0;
}

.pin-icon {
  color: #f39c12;
}

.status-tag {
  margin-left: 10px;
}

.task-actions {
  display: flex;
  gap: 10px;
}

.task-content {
  margin-top: 20px;
}

.description-card,
.skills-card,
.schedule-card,
.collaborators-card {
  margin-top: 20px;
}

.collaborators-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.collaborators-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.man-days-summary {
  font-size: 13px;
  color: #666;
}

.collaborators-empty {
  padding: 10px 0;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.developer-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dev-name {
  font-weight: 500;
}

.dev-username {
  font-size: 12px;
  color: #999;
}

.description-content {
  min-height: 100px;
  line-height: 1.6;
}

.skills-content {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.skill-tag {
  margin: 0;
}

.text-muted {
  color: #999;
}
</style>
