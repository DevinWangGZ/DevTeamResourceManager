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
              v-if="canSubmit"
              type="primary"
              @click="showSubmitDialog = true"
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
      </div>
    </el-card>

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
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import MarkdownViewer from '@/components/ui/MarkdownViewer.vue'
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
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
  pinTask,
  getTaskSchedule,
  type TaskDetail,
} from '@/api/task'

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

const submitRules: FormRules = {
  actual_man_days: [{ required: true, message: '请输入实际投入人天', trigger: 'blur' }],
}

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
  // 只有任务的创建者（且是项目经理或系统管理员）才能发布草稿状态的任务
  const isCreator = task.value.creator_id === userStore.userInfo.id
  const isManager = userStore.userInfo.role === 'project_manager' || userStore.userInfo.role === 'system_admin'
  const isDraft = task.value.status === 'draft'
  
  // 调试信息（开发环境）
  if (import.meta.env.DEV) {
    console.debug('发布按钮显示条件:', {
      isDraft,
      isCreator,
      isManager,
      creatorId: task.value.creator_id,
      currentUserId: userStore.userInfo.id,
      currentUserRole: userStore.userInfo.role,
    })
  }
  
  return isDraft && isCreator && isManager
})

const canClaim = computed(() => {
  return (
    task.value?.status === 'published' &&
    userStore.userInfo?.role === 'developer'
  )
})

const canEvaluate = computed(() => {
  return (
    task.value?.status === 'pending_eval' &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
  )
})

const canStart = computed(() => {
  return (
    task.value?.status === 'claimed' &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
  )
})

const canSubmit = computed(() => {
  return (
    (task.value?.status === 'claimed' || task.value?.status === 'in_progress') &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
  )
})

const canConfirm = computed(() => {
  return (
    task.value?.status === 'submitted' &&
    (userStore.userInfo?.role === 'project_manager' || userStore.userInfo?.role === 'system_admin')
  )
})

const canPin = computed(() => {
  return (
    (task.value?.status === 'claimed' || task.value?.status === 'in_progress') &&
    task.value?.assignee_id === userStore.userInfo?.id &&
    userStore.userInfo?.role === 'developer'
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
    // 加载排期信息
    if (task.value.assignee_id) {
      try {
        schedule.value = await getTaskSchedule(taskId)
      } catch (error) {
        // 排期信息可能不存在，忽略错误
      }
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载任务详情失败')
    router.push('/tasks')
  } finally {
    loading.value = false
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
.schedule-card {
  margin-top: 20px;
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
