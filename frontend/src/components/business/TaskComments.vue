<template>
  <div class="task-comments">
    <!-- 留言输入区 -->
    <div class="comment-input-area">
      <el-avatar :size="32" class="user-avatar">
        {{ currentUserInitial }}
      </el-avatar>
      <div class="input-wrapper">
        <el-input
          v-model="newComment"
          type="textarea"
          :rows="2"
          placeholder="留言备注，任务参与者均可查看..."
          maxlength="2000"
          show-word-limit
          resize="none"
          @keydown.ctrl.enter="submitComment"
        />
        <div class="input-actions">
          <span class="input-hint">Ctrl + Enter 发送</span>
          <el-button
            type="primary"
            size="small"
            :loading="submitting"
            :disabled="!newComment.trim()"
            @click="submitComment"
          >
            发送留言
          </el-button>
        </div>
      </div>
    </div>

    <!-- 留言列表 -->
    <div v-loading="loading" class="comment-list">
      <template v-if="comments.length > 0">
        <div
          v-for="comment in comments"
          :key="comment.id"
          class="comment-item"
        >
          <el-avatar :size="32" class="user-avatar comment-avatar">
            {{ getInitial(comment.user_full_name || comment.user_name) }}
          </el-avatar>
          <div class="comment-body">
            <div class="comment-meta">
              <span class="comment-author">{{ comment.user_full_name || comment.user_name }}</span>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              <span
                v-if="comment.updated_at !== comment.created_at"
                class="comment-edited"
              >（已编辑）</span>
            </div>

            <!-- 展示模式 -->
            <template v-if="editingId !== comment.id">
              <div class="comment-content">{{ comment.content }}</div>
              <div v-if="comment.user_id === currentUserId" class="comment-actions">
                <el-button link size="small" @click="startEdit(comment)">编辑</el-button>
                <el-popconfirm
                  title="确定删除这条留言吗？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm="handleDelete(comment.id)"
                >
                  <template #reference>
                    <el-button link size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>

            <!-- 编辑模式 -->
            <template v-else>
              <el-input
                v-model="editContent"
                type="textarea"
                :rows="2"
                maxlength="2000"
                show-word-limit
                resize="none"
                autofocus
              />
              <div class="edit-actions">
                <el-button size="small" @click="cancelEdit">取消</el-button>
                <el-button
                  size="small"
                  type="primary"
                  :loading="updating"
                  :disabled="!editContent.trim()"
                  @click="saveEdit(comment.id)"
                >
                  保存
                </el-button>
              </div>
            </template>
          </div>
        </div>
      </template>
      <div v-else class="empty-comments">
        <el-empty description="暂无留言，来发第一条吧~" :image-size="64" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  getTaskComments,
  createTaskComment,
  updateTaskComment,
  deleteTaskComment,
  type TaskComment,
} from '@/api/task'

const props = defineProps<{
  taskId: number
}>()

const emit = defineEmits<{
  (e: 'count-change', count: number): void
}>()

const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.id ?? 0)
const currentUserInitial = computed(() => {
  const name = userStore.userInfo?.full_name || userStore.userInfo?.username || '?'
  return getInitial(name)
})

const loading = ref(false)
const submitting = ref(false)
const updating = ref(false)
const comments = ref<TaskComment[]>([])
const newComment = ref('')
const editingId = ref<number | null>(null)
const editContent = ref('')

const getInitial = (name: string) => (name ? name.charAt(0).toUpperCase() : '?')

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const loadComments = async () => {
  loading.value = true
  try {
    const res = await getTaskComments(props.taskId)
    comments.value = res.items
    emit('count-change', res.total)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载留言失败')
  } finally {
    loading.value = false
  }
}

const submitComment = async () => {
  const content = newComment.value.trim()
  if (!content) return
  submitting.value = true
  try {
    const comment = await createTaskComment(props.taskId, content)
    comments.value.unshift(comment)
    newComment.value = ''
    emit('count-change', comments.value.length)
    ElMessage.success('留言发送成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送留言失败')
  } finally {
    submitting.value = false
  }
}

const startEdit = (comment: TaskComment) => {
  editingId.value = comment.id
  editContent.value = comment.content
}

const cancelEdit = () => {
  editingId.value = null
  editContent.value = ''
}

const saveEdit = async (commentId: number) => {
  const content = editContent.value.trim()
  if (!content) return
  updating.value = true
  try {
    const updated = await updateTaskComment(commentId, content)
    const idx = comments.value.findIndex(c => c.id === commentId)
    if (idx !== -1) comments.value[idx] = updated
    cancelEdit()
    ElMessage.success('留言已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '更新留言失败')
  } finally {
    updating.value = false
  }
}

const handleDelete = async (commentId: number) => {
  try {
    await deleteTaskComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
    emit('count-change', comments.value.length)
    ElMessage.success('留言已删除')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除留言失败')
  }
}

onMounted(loadComments)
watch(() => props.taskId, loadComments)

defineExpose({ loadComments })
</script>

<style scoped>
.task-comments {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-input-area {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.user-avatar {
  background-color: #409eff;
  color: #fff;
  font-weight: bold;
  flex-shrink: 0;
}

.input-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.input-hint {
  font-size: 12px;
  color: #c0c4cc;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.comment-avatar {
  background-color: #67c23a;
  margin-top: 2px;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.comment-author {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.comment-time {
  font-size: 12px;
  color: #909399;
}

.comment-edited {
  font-size: 12px;
  color: #c0c4cc;
}

.comment-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background-color: #f5f7fa;
  border-radius: 6px;
  padding: 10px 14px;
}

.comment-actions {
  display: flex;
  gap: 4px;
  margin-top: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.comment-item:hover .comment-actions {
  opacity: 1;
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.empty-comments {
  padding: 20px 0;
}
</style>
