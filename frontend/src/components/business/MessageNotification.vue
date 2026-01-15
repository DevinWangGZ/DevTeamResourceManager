<template>
  <div class="message-notification">
    <el-dropdown trigger="click" @command="handleCommand">
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="message-badge">
        <el-button :icon="Bell" circle />
      </el-badge>
      <template #dropdown>
        <el-dropdown-menu class="message-dropdown">
          <div class="dropdown-header">
            <span>消息通知</span>
            <el-button link type="primary" size="small" @click="goToMessageCenter">
              查看全部
            </el-button>
          </div>
          <div class="message-list" v-loading="loading">
            <div v-if="recentMessages.length === 0" class="empty-message">
              <el-empty description="暂无消息" :image-size="80" />
            </div>
            <div
              v-for="message in recentMessages"
              :key="message.id"
              :class="['message-item', { 'unread': !message.is_read }]"
              @click="handleMessageClick(message)"
            >
              <div class="message-content">
                <div class="message-title">{{ message.title }}</div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>
          </div>
          <div class="dropdown-footer">
            <el-button link type="primary" size="small" @click.stop="markAllAsReadHandler" :disabled="unreadCount === 0">
              全部标记为已读
            </el-button>
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { getMessages, getUnreadCount, markAsRead, markAllAsRead, type Message } from '@/api/message'

const router = useRouter()

const loading = ref(false)
const unreadCount = ref(0)
const recentMessages = ref<Message[]>([])
let refreshTimer: number | null = null

const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

const loadUnreadCount = async () => {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data.unread_count
  } catch (error: any) {
    console.error('加载未读消息数量失败:', error)
  }
}

const loadRecentMessages = async () => {
  loading.value = true
  try {
    const data = await getMessages({ page: 1, page_size: 5 })
    recentMessages.value = data.items
  } catch (error: any) {
    console.error('加载最近消息失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadUnreadCount()
  loadRecentMessages()
}

const handleCommand = (command: string) => {
  if (command === 'center') {
    goToMessageCenter()
  }
}

const handleMessageClick = async (message: Message) => {
  // 如果未读，自动标记为已读
  if (!message.is_read) {
    try {
      await markAsRead(message.id)
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error: any) {
      console.error('标记消息已读失败:', error)
    }
  }

  // 如果有关联任务，跳转到任务详情
  if (message.related_task_id) {
    router.push({ name: 'TaskDetail', params: { id: message.related_task_id } })
  } else {
    // 否则跳转到消息中心
    goToMessageCenter()
  }
}

const markAllAsReadHandler = async () => {
  try {
    await markAllAsRead()
    ElMessage.success('已标记所有消息为已读')
    refreshData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const goToMessageCenter = () => {
  router.push('/messages')
}

onMounted(() => {
  refreshData()
  // 每30秒刷新一次未读消息数量
  refreshTimer = window.setInterval(() => {
    loadUnreadCount()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.message-notification {
  display: inline-block;
}

.message-badge {
  cursor: pointer;
}

.message-dropdown {
  width: 350px;
  max-height: 500px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

.message-list {
  max-height: 400px;
  overflow-y: auto;
}

.empty-message {
  padding: 20px;
  text-align: center;
}

.message-item {
  padding: 12px 15px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.message-item:hover {
  background-color: #f5f7fa;
}

.message-item.unread {
  background-color: #ecf5ff;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.message-title {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.dropdown-footer {
  padding: 10px 15px;
  border-top: 1px solid #ebeef5;
  text-align: center;
}
</style>
