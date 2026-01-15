<template>
  <div class="message-center-container">
    <Breadcrumb />
    
    <div class="page-header">
      <h2>消息中心</h2>
      <div class="header-actions">
        <el-button @click="markAllAsReadHandler" :disabled="unreadCount === 0">
          全部标记为已读
        </el-button>
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="消息类型">
          <el-select v-model="filterForm.type" placeholder="全部类型" clearable style="width: 200px">
            <el-option label="任务状态变更" value="task_status_change" />
            <el-option label="待办提醒" value="todo_reminder" />
            <el-option label="系统通知" value="system_notice" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.is_read" placeholder="全部" clearable style="width: 150px">
            <el-option label="未读" :value="false" />
            <el-option label="已读" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadMessages">筛选</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 消息统计 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">未读消息</div>
            <div class="stat-value text-danger">{{ unreadCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">总消息数</div>
            <div class="stat-value">{{ total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">已读消息</div>
            <div class="stat-value text-success">{{ total - unreadCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 消息列表 -->
    <el-card style="margin-top: 20px" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>消息列表</span>
          <span class="header-info">共 {{ total }} 条消息</span>
        </div>
      </template>

      <div v-if="messages.length === 0" class="empty-state">
        <el-empty description="暂无消息" :image-size="150" />
      </div>

      <div v-else class="message-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'unread': !message.is_read }]"
          @click="handleMessageClick(message)"
        >
          <div class="message-content">
            <div class="message-header">
              <el-tag :type="getMessageTypeTag(message.type)" size="small" class="message-type-tag">
                {{ getMessageTypeText(message.type) }}
              </el-tag>
              <span class="message-title">{{ message.title }}</span>
              <el-badge v-if="!message.is_read" :value="1" class="unread-badge" />
            </div>
            <div class="message-body" v-if="message.content">
              <p>{{ message.content }}</p>
            </div>
            <div class="message-footer">
              <span class="message-time">{{ formatDateTime(message.created_at) }}</span>
              <div class="message-actions">
                <el-button
                  v-if="!message.is_read"
                  link
                  type="primary"
                  size="small"
                  @click.stop="markAsReadHandler(message.id)"
                >
                  标记已读
                </el-button>
                <el-button
                  link
                  type="danger"
                  size="small"
                  @click.stop="handleDelete(message.id)"
                >
                  删除
                </el-button>
                <el-button
                  v-if="message.related_task_id"
                  link
                  type="primary"
                  size="small"
                  @click.stop="viewTask(message.related_task_id)"
                >
                  查看任务
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import { getMessages, getUnreadCount, markAsRead as markAsReadAPI, markAllAsRead as markAllAsReadAPI, deleteMessage, type Message } from '@/api/message'

const router = useRouter()

const loading = ref(false)
const messages = ref<Message[]>([])
const total = ref(0)
const unreadCount = ref(0)

const filterForm = reactive({
  type: undefined as string | undefined,
  is_read: undefined as boolean | undefined,
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
})

const getMessageTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    task_status_change: '任务状态变更',
    todo_reminder: '待办提醒',
    system_notice: '系统通知',
  }
  return typeMap[type] || type
}

const getMessageTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    task_status_change: 'primary',
    todo_reminder: 'warning',
    system_notice: 'info',
  }
  return tagMap[type] || ''
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadMessages = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    if (filterForm.type) {
      params.type = filterForm.type
    }

    if (filterForm.is_read !== undefined) {
      params.is_read = filterForm.is_read
    }

    const data = await getMessages(params)
    messages.value = data.items
    total.value = data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载消息失败')
  } finally {
    loading.value = false
  }
}

const loadUnreadCount = async () => {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data.unread_count
  } catch (error: any) {
    console.error('加载未读消息数量失败:', error)
  }
}

const refreshData = () => {
  loadMessages()
  loadUnreadCount()
}

const resetFilter = () => {
  filterForm.type = undefined
  filterForm.is_read = undefined
  pagination.page = 1
  loadMessages()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadMessages()
}

const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadMessages()
}

const handleMessageClick = async (message: Message) => {
  // 如果未读，自动标记为已读
  if (!message.is_read) {
    try {
      await markAsReadAPI(message.id)
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error: any) {
      console.error('标记消息已读失败:', error)
    }
  }

  // 如果有关联任务，跳转到任务详情
  if (message.related_task_id) {
    router.push({ name: 'TaskDetail', params: { id: message.related_task_id } })
  }
}

const markAsReadHandler = async (messageId: number) => {
  try {
    await markAsReadAPI(messageId)
    const message = messages.value.find(m => m.id === messageId)
    if (message) {
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    ElMessage.success('已标记为已读')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '标记失败')
  }
}

const markAllAsReadHandler = async () => {
  try {
    await ElMessageBox.confirm('确定要标记所有消息为已读吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await markAllAsReadAPI(filterForm.type)
    ElMessage.success('已标记所有消息为已读')
    refreshData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

const handleDelete = async (messageId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMessage(messageId)
    ElMessage.success('消息已删除')
    loadMessages()
    loadUnreadCount()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

onMounted(() => {
  loadMessages()
  loadUnreadCount()
})
</script>

<style scoped>
.message-center-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px 0;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.text-danger {
  color: #f56c6c;
}

.text-success {
  color: #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  font-size: 14px;
  color: #666;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.message-item:hover {
  background-color: #f5f7fa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-item.unread {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
}

.message-content {
  width: 100%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.message-type-tag {
  flex-shrink: 0;
}

.message-title {
  flex: 1;
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.unread-badge {
  flex-shrink: 0;
}

.message-body {
  margin-bottom: 10px;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.message-time {
  flex-shrink: 0;
}

.message-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
