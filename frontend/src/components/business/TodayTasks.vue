<template>
  <el-card class="today-tasks-card" shadow="never">
    <template #header>
      <div class="today-header">
        <div class="today-header-left">
          <el-icon class="today-icon"><Sunny /></el-icon>
          <span class="today-title">今日任务</span>
          <el-tag type="primary" size="small" style="margin-left: 8px">
            {{ todayStr }}
          </el-tag>
          <el-badge
            v-if="tasks.length > 0"
            :value="tasks.length"
            type="primary"
            style="margin-left: 10px"
          />
        </div>
        <el-button link type="primary" size="small" @click="$router.push('/tasks')">
          查看全部任务 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="tasks.length === 0" class="today-empty">
      <el-empty description="今天暂无待处理任务，去任务集市看看？" :image-size="72">
        <el-button type="primary" size="small" @click="$router.push('/marketplace')">
          前往任务集市
        </el-button>
      </el-empty>
    </div>

    <!-- 任务列表 -->
    <div v-else class="today-list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="today-item"
        :class="{ 'is-overdue': isOverdue(task) }"
      >
        <!-- 左侧信息 -->
        <div class="today-item-info" @click="viewTask(task.id)">
          <div class="today-item-title-row">
            <el-tag
              v-if="task.priority && task.priority !== 'P2'"
              :type="task.priority === 'P0' ? 'danger' : 'warning'"
              size="small"
              effect="dark"
              class="priority-badge"
            >
              {{ task.priority }}
            </el-tag>
            <el-tag
              v-if="task.is_collaborator"
              type="info"
              size="small"
              class="collab-badge"
            >
              协助
            </el-tag>
            <span class="today-item-title">{{ task.title }}</span>
          </div>
          <div class="today-item-meta">
            <el-tag :type="getStatusType(task.status)" size="small">
              {{ getStatusText(task.status) }}
            </el-tag>
            <span v-if="task.end_date" class="meta-item">
              <el-icon><Calendar /></el-icon>
              排期至 {{ task.end_date }}
            </span>
            <span v-if="task.deadline" class="meta-item" :class="{ 'text-danger': isDeadlineNear(task.deadline) }">
              <el-icon><Warning /></el-icon>
              截止 {{ task.deadline }}
            </span>
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              拟 {{ task.estimated_man_days ?? '-' }} 人天
            </span>
          </div>
        </div>

        <!-- 右侧快捷操作 -->
        <div class="today-item-actions">
          <!-- 留言 -->
          <el-tooltip content="快速留言" placement="top">
            <el-button
              circle
              size="small"
              @click.stop="openCommentDialog(task)"
            >
              <el-icon><ChatDotSquare /></el-icon>
            </el-button>
          </el-tooltip>

          <!-- 提交（仅认领人且状态为进行中可提交） -->
          <el-tooltip
            v-if="canSubmit(task)"
            content="提交任务"
            placement="top"
          >
            <el-button
              circle
              size="small"
              type="primary"
              @click.stop="openSubmitDialog(task)"
            >
              <el-icon><Upload /></el-icon>
            </el-button>
          </el-tooltip>

          <!-- 开始（已认领 -> 进行中） -->
          <el-tooltip
            v-if="canStart(task)"
            content="开始任务"
            placement="top"
          >
            <el-button
              circle
              size="small"
              type="success"
              @click.stop="handleStart(task)"
            >
              <el-icon><CaretRight /></el-icon>
            </el-button>
          </el-tooltip>

          <!-- 查看详情 -->
          <el-tooltip content="查看详情" placement="top">
            <el-button
              circle
              size="small"
              @click.stop="viewTask(task.id)"
            >
              <el-icon><View /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- 快速留言对话框 -->
    <el-dialog
      v-model="showCommentDialog"
      :title="`留言：${commentingTask?.title}`"
      width="480px"
      @close="commentContent = ''"
    >
      <el-input
        v-model="commentContent"
        type="textarea"
        :rows="4"
        placeholder="输入留言内容..."
        maxlength="2000"
        show-word-limit
        autofocus
      />
      <template #footer>
        <el-button @click="showCommentDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="commentLoading"
          :disabled="!commentContent.trim()"
          @click="submitComment"
        >
          发送
        </el-button>
      </template>
    </el-dialog>

    <!-- 快速提交对话框 -->
    <el-dialog
      v-model="showSubmitDialog_"
      :title="`提交任务：${submittingTask?.title}`"
      width="440px"
    >
      <el-form label-width="110px">
        <el-form-item label="实际投入人天">
          <el-input-number
            v-model="actualManDays"
            :min="0.01"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog_ = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitLoading"
          :disabled="!actualManDays"
          @click="doSubmit"
        >
          提交
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Sunny,
  ArrowRight,
  ChatDotSquare,
  Upload,
  View,
  Calendar,
  Warning,
  Timer,
  CaretRight,
} from '@element-plus/icons-vue'
import { createTaskComment, startTask, submitTask } from '@/api/task'
import { useUserStore } from '@/stores/user'
import type { TodayTask } from '@/api/dashboard'

const props = defineProps<{
  tasks: TodayTask[]
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const router = useRouter()
const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.id ?? 0)

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    claimed: '已认领',
    in_progress: '进行中',
    pending_eval: '待评估',
    submitted: '已提交',
  }
  return map[status] || status
}

const getStatusType = (status: string): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    claimed: 'primary',
    in_progress: 'primary',
    pending_eval: 'warning',
    submitted: 'warning',
  }
  return map[status] || 'info'
}

const isOverdue = (task: TodayTask) => {
  if (!task.deadline) return false
  return new Date(task.deadline) < new Date()
}

const isDeadlineNear = (deadline: string) => {
  const d = new Date(deadline)
  const diff = d.getTime() - Date.now()
  return diff >= 0 && diff < 3 * 86400000
}

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

// 只有非协助人且状态为 in_progress 才可提交
const canSubmit = (task: TodayTask) => !task.is_collaborator && task.status === 'in_progress'
// 只有非协助人且状态为 claimed 才可开始
const canStart = (task: TodayTask) => !task.is_collaborator && task.status === 'claimed'

// ── 快速留言 ──────────────────────────────────────────────────────────────────
const showCommentDialog = ref(false)
const commentingTask = ref<TodayTask | null>(null)
const commentContent = ref('')
const commentLoading = ref(false)

const openCommentDialog = (task: TodayTask) => {
  commentingTask.value = task
  commentContent.value = ''
  showCommentDialog.value = true
}

const submitComment = async () => {
  if (!commentingTask.value || !commentContent.value.trim()) return
  commentLoading.value = true
  try {
    await createTaskComment(commentingTask.value.id, commentContent.value.trim())
    ElMessage.success('留言发送成功')
    showCommentDialog.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    commentLoading.value = false
  }
}

// ── 快速提交 ──────────────────────────────────────────────────────────────────
const showSubmitDialog_ = ref(false)
const submittingTask = ref<TodayTask | null>(null)
const actualManDays = ref<number | undefined>(undefined)
const submitLoading = ref(false)

const openSubmitDialog = (task: TodayTask) => {
  submittingTask.value = task
  actualManDays.value = task.estimated_man_days
  showSubmitDialog_.value = true
}

const doSubmit = async () => {
  if (!submittingTask.value || !actualManDays.value) return
  submitLoading.value = true
  try {
    await submitTask(submittingTask.value.id, { actual_man_days: actualManDays.value })
    ElMessage.success('任务已提交')
    showSubmitDialog_.value = false
    emit('refresh')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ── 开始任务 ──────────────────────────────────────────────────────────────────
const handleStart = async (task: TodayTask) => {
  try {
    await startTask(task.id)
    ElMessage.success('任务已开始')
    emit('refresh')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}
</script>

<style scoped>
.today-tasks-card {
  margin-bottom: 4px;
}

.today-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.today-header-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.today-icon {
  font-size: 18px;
  color: #e6a23c;
}

.today-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

.today-empty {
  padding: 16px 0;
}

.today-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.today-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  background: #fafafa;
  transition: box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  gap: 12px;
}

.today-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.12);
}

.today-item.is-overdue {
  border-color: #f56c6c;
  background: #fff0f0;
}

.today-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.today-item-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.today-item-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.priority-badge,
.collab-badge {
  flex-shrink: 0;
}

.today-item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #909399;
}

.text-danger {
  color: #f56c6c;
}

.today-item-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
</style>
