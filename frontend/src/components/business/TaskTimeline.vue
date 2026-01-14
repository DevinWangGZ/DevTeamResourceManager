<template>
  <div class="task-timeline-container">
    <div v-if="timelineData.length === 0" class="empty-state">
      <el-empty description="暂无任务数据" :image-size="100" />
    </div>
    <div v-else class="timeline-wrapper">
      <el-timeline>
        <el-timeline-item
          v-for="(item, index) in timelineData"
          :key="index"
          :timestamp="item.timestamp"
          :type="item.type"
          :color="item.color"
          placement="top"
        >
          <el-card class="timeline-card">
            <div class="card-header">
              <h4>{{ item.title }}</h4>
              <el-tag :type="getStatusType(item.status)" size="small">
                {{ getStatusText(item.status) }}
              </el-tag>
            </div>
            <div class="card-content">
              <div class="info-row">
                <span class="label">创建者:</span>
                <span>{{ item.creator_name || '未知' }}</span>
              </div>
              <div class="info-row" v-if="item.assignee_name">
                <span class="label">认领者:</span>
                <span>{{ item.assignee_name }}</span>
              </div>
              <div class="info-row">
                <span class="label">拟投入人天:</span>
                <span>{{ item.estimated_man_days }} 人天</span>
              </div>
              <div class="info-row" v-if="item.actual_man_days">
                <span class="label">实际投入人天:</span>
                <span>{{ item.actual_man_days }} 人天</span>
              </div>
              <div class="info-row" v-if="item.schedule">
                <span class="label">排期:</span>
                <span>
                  {{ formatDate(item.schedule.start_date) }} ~ {{ formatDate(item.schedule.end_date) }}
                  <el-tag v-if="item.schedule.is_pinned" type="warning" size="small" style="margin-left: 8px">
                    已置顶
                  </el-tag>
                </span>
              </div>
            </div>
            <div class="card-footer">
              <el-button link type="primary" size="small" @click="viewTask(item.id)">
                查看详情
              </el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { ProjectTask } from '@/api/project'

interface Props {
  tasks: ProjectTask[]
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

const getTimelineType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: '',
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

const getTimelineColor = (status: string) => {
  const colorMap: Record<string, string> = {
    draft: '#909399',
    published: '#67c23a',
    pending_eval: '#e6a23c',
    claimed: '#409eff',
    in_progress: '#409eff',
    submitted: '#e6a23c',
    confirmed: '#67c23a',
    archived: '#909399',
  }
  return colorMap[status] || '#409eff'
}

const timelineData = computed(() => {
  return props.tasks
    .map(task => ({
      id: task.id,
      title: task.title,
      status: task.status,
      creator_name: task.creator_name,
      assignee_name: task.assignee_name,
      estimated_man_days: task.estimated_man_days,
      actual_man_days: task.actual_man_days,
      schedule: task.schedule,
      timestamp: task.created_at
        ? new Date(task.created_at).toLocaleString('zh-CN')
        : '',
      type: getTimelineType(task.status),
      color: getTimelineColor(task.status),
    }))
    .sort((a, b) => {
      // 按创建时间倒序排列
      const dateA = a.timestamp ? new Date(a.timestamp).getTime() : 0
      const dateB = b.timestamp ? new Date(b.timestamp).getTime() : 0
      return dateB - dateA
    })
})

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}
</script>

<style scoped>
.task-timeline-container {
  padding: 20px;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.timeline-wrapper {
  max-width: 1000px;
  margin: 0 auto;
}

.timeline-card {
  margin-bottom: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.info-row .label {
  color: #666;
  min-width: 100px;
}

.card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}
</style>
