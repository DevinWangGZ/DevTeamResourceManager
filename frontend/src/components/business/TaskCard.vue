<template>
  <el-card class="task-card" shadow="hover" @click="handleClick">
    <template #header>
      <div class="card-header">
        <div class="task-title">
          <span class="title-text">{{ task.title }}</span>
        </div>
        <el-tag :type="getStatusType(task.status)" size="small">
          {{ getStatusText(task.status) }}
        </el-tag>
      </div>
    </template>

    <div class="card-content">
      <div class="task-info">
        <div class="info-item" v-if="task.project_name">
          <el-icon><FolderOpened /></el-icon>
          <span>{{ task.project_name }}</span>
        </div>
        <div class="info-item">
          <el-icon><User /></el-icon>
          <span>{{ task.creator_name || '未知' }}</span>
        </div>
        <div class="info-item">
          <el-icon><Clock /></el-icon>
          <span>{{ task.estimated_man_days }} 人天</span>
        </div>
        <div class="info-item" v-if="task.deadline">
          <el-icon><Calendar /></el-icon>
          <span>{{ formatDate(task.deadline) }}</span>
        </div>
      </div>

      <div class="task-description" v-if="task.description">
        <p>{{ truncateDescription(task.description) }}</p>
      </div>

      <div class="task-skills" v-if="task.required_skills">
        <el-tag
          v-for="(skill, index) in getSkillsList(task.required_skills)"
          :key="index"
          size="small"
          class="skill-tag"
        >
          {{ skill }}
        </el-tag>
      </div>
    </div>

    <template #footer>
      <div class="card-footer">
        <el-button type="primary" size="small" @click.stop="handleClaim">
          认领任务
        </el-button>
        <el-button link type="primary" size="small" @click.stop="handleView">
          查看详情
        </el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  User,
  Clock,
  Calendar,
} from '@element-plus/icons-vue'
import type { MarketplaceTask } from '@/api/task'
import { claimTask } from '@/api/task'

interface Props {
  task: MarketplaceTask
}

const props = defineProps<Props>()
const router = useRouter()

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
    claimed: 'primary',
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

const truncateDescription = (description: string, maxLength: number = 100) => {
  if (!description) return ''
  // 移除Markdown标记
  const plainText = description.replace(/[#*`\[\]]/g, '').trim()
  if (plainText.length <= maxLength) return plainText
  return plainText.substring(0, maxLength) + '...'
}

const getSkillsList = (skills?: string) => {
  if (!skills) return []
  return skills.split(',').map(s => s.trim()).filter(s => s).slice(0, 5) // 最多显示5个技能
}

const handleClick = () => {
  router.push({ name: 'TaskDetail', params: { id: props.task.id } })
}

const handleView = () => {
  router.push({ name: 'TaskDetail', params: { id: props.task.id } })
}

const handleClaim = async () => {
  try {
    await ElMessageBox.confirm('确定要认领此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await claimTask(props.task.id)
    ElMessage.success('任务认领成功')
    // 触发父组件刷新
    emit('claimed', props.task.id)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '认领任务失败')
    }
  }
}

const emit = defineEmits<{
  claimed: [taskId: number]
}>()
</script>

<style scoped>
.task-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.pin-icon {
  color: #f39c12;
  font-size: 16px;
}

.title-text {
  font-weight: 600;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-content {
  flex: 1;
  padding: 10px 0;
}

.task-info {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #666;
}

.task-description {
  margin-bottom: 12px;
  min-height: 40px;
}

.task-description p {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.skill-tag {
  margin: 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}
</style>
