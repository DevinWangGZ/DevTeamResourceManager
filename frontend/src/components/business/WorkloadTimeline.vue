<template>
  <div class="workload-timeline-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Calendar /></el-icon>
          <span>{{ title }}</span>
          <div class="view-switch">
            <el-radio-group v-model="viewType" size="small" @change="handleViewChange">
              <el-radio-button label="week">周视图</el-radio-button>
              <el-radio-button label="month">月视图</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="timeline-content">
        <!-- 时间轴 -->
        <div class="timeline-wrapper" ref="timelineRef">
          <div
            v-for="(item, index) in timelineData"
            :key="index"
            class="timeline-item"
            :class="getWorkloadStatusClass(item.workload)"
          >
            <div class="timeline-date">
              <div class="date-label">{{ formatDate(item.date) }}</div>
              <div class="workload-value">{{ item.workload.toFixed(1) }} 人天</div>
            </div>
            <div class="timeline-bar">
              <div
                class="workload-bar"
                :style="{ width: `${getWorkloadPercentage(item.workload)}%` }"
              ></div>
            </div>
            <div class="timeline-tasks" v-if="item.tasks && item.tasks.length > 0">
              <el-tag
                v-for="task in item.tasks"
                :key="task.id"
                :type="getTaskStatusType(task.status)"
                size="small"
                class="task-tag"
              >
                {{ task.title }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 图例 -->
        <div class="legend">
          <div class="legend-item">
            <div class="legend-color overloaded"></div>
            <span>过载 (>120%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color normal"></div>
            <span>正常 (80%-120%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color idle"></div>
            <span>空闲 (<80%)</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getWorkloadTimeline, type WorkloadTimelineItem } from '@/api/workload'

interface Props {
  title?: string
  userId?: number
  startDate?: string
  endDate?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '工作负荷时间轴',
  userId: undefined,
  startDate: undefined,
  endDate: undefined,
})

const loading = ref(false)
const viewType = ref<'week' | 'month'>('week')
const timelineRef = ref<HTMLDivElement>()
const workloadData = ref<WorkloadTimelineItem[]>([])

// 计算时间轴数据
const timelineData = computed(() => {
  if (!workloadData.value || workloadData.value.length === 0) {
    return []
  }

  // 根据视图类型生成时间轴
  const data: Array<{
    date: string
    workload: number
    tasks?: Array<{ id: number; title: string; status: string }>
  }> = []

  if (viewType.value === 'week') {
    // 周视图：显示最近4周
    const today = new Date()
    for (let i = 3; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i * 7)
      const weekStart = new Date(date)
      weekStart.setDate(date.getDate() - date.getDay()) // 周一开始
      
      // 获取ISO周号
      const weekNum = getISOWeek(weekStart)
      const weekKey = `${weekStart.getFullYear()}-W${weekNum.toString().padStart(2, '0')}`

      // 查找该周的工作量数据
      const weekData = workloadData.value.find((item) => {
        const periodStart = new Date(item.period_start)
        const periodEnd = new Date(item.period_end)
        return periodStart <= weekStart && weekStart <= periodEnd
      })

      data.push({
        date: weekStart.toISOString().split('T')[0],
        workload: weekData ? weekData.total_man_days : 0,
        tasks: weekData?.tasks || [],
      })
    }
  } else {
    // 月视图：显示最近6个月
    const today = new Date()
    for (let i = 5; i >= 0; i--) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1)
      const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)

      // 查找该月的工作量数据
      const monthData = workloadData.value.filter((item) => {
        const periodStart = new Date(item.period_start)
        return (
          periodStart.getFullYear() === monthStart.getFullYear() &&
          periodStart.getMonth() === monthStart.getMonth()
        )
      })

      const totalWorkload = monthData.reduce(
        (sum, item) => sum + item.total_man_days,
        0
      )
      
      // 合并所有任务（去重）
      const allTasks = monthData.flatMap(item => item.tasks || [])
      const uniqueTasks = Array.from(
        new Map(allTasks.map(task => [task.id, task])).values()
      )

      data.push({
        date: monthStart.toISOString().split('T')[0],
        workload: totalWorkload,
        tasks: uniqueTasks,
      })
    }
  }

  return data
})

// 获取ISO周号
function getISOWeek(date: Date): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = d.getUTCDay() || 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  if (viewType.value === 'week') {
    return `${date.getMonth() + 1}/${date.getDate()}`
  } else {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
  }
}

const getWorkloadPercentage = (workload: number) => {
  // 假设每天标准工作量为1人天，一周5个工作日
  const maxWorkload = viewType.value === 'week' ? 5 : 22 // 周：5天，月：22天
  return Math.min((workload / maxWorkload) * 100, 100)
}

const getWorkloadStatusClass = (workload: number) => {
  const percentage = getWorkloadPercentage(workload)
  if (percentage > 120) return 'overloaded'
  if (percentage >= 80) return 'normal'
  return 'idle'
}

const getTaskStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    claimed: 'primary',
    in_progress: 'warning',
    submitted: 'info',
    confirmed: 'success',
  }
  return typeMap[status] || 'info'
}

const handleViewChange = () => {
  loadWorkloadData()
}

const loadWorkloadData = async () => {
  loading.value = true
  try {
    const today = new Date()
    let startDate: string
    let endDate: string

    if (viewType.value === 'week') {
      // 最近4周 + 未来1周
      const start = new Date(today)
      start.setDate(start.getDate() - 28)
      startDate = start.toISOString().split('T')[0]
      const end = new Date(today)
      end.setDate(end.getDate() + 7)
      endDate = end.toISOString().split('T')[0]
    } else {
      // 最近6个月 + 未来1个月
      const start = new Date(today.getFullYear(), today.getMonth() - 6, 1)
      startDate = start.toISOString().split('T')[0]
      const end = new Date(today.getFullYear(), today.getMonth() + 1, 1)
      endDate = end.toISOString().split('T')[0]
    }

    const result = await getWorkloadTimeline({
      start_date: props.startDate || startDate,
      end_date: props.endDate || endDate,
    })

    workloadData.value = result.items
  } catch (error: any) {
    console.error('加载负荷数据失败:', error)
    ElMessage.error('加载工作负荷数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadWorkloadData()
})
</script>

<style scoped>
.workload-timeline-container {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.view-switch {
  margin-left: auto;
}

.timeline-content {
  padding: 20px 0;
}

.timeline-wrapper {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-radius: 8px;
  background-color: #f5f7fa;
  transition: all 0.3s;
}

.timeline-item:hover {
  background-color: #e4e7ed;
}

.timeline-item.overloaded {
  border-left: 4px solid #f56c6c;
}

.timeline-item.normal {
  border-left: 4px solid #e6a23c;
}

.timeline-item.idle {
  border-left: 4px solid #67c23a;
}

.timeline-date {
  min-width: 120px;
  text-align: center;
}

.date-label {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.workload-value {
  font-size: 12px;
  color: #666;
}

.timeline-bar {
  flex: 1;
  height: 30px;
  background-color: #e4e7ed;
  border-radius: 15px;
  overflow: hidden;
  position: relative;
}

.workload-bar {
  height: 100%;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 50%, #e6a23c 80%, #f56c6c 100%);
  transition: width 0.3s;
}

.timeline-item.overloaded .workload-bar {
  background: linear-gradient(90deg, #f56c6c 0%, #f56c6c 100%);
}

.timeline-item.normal .workload-bar {
  background: linear-gradient(90deg, #e6a23c 0%, #e6a23c 100%);
}

.timeline-item.idle .workload-bar {
  background: linear-gradient(90deg, #67c23a 0%, #67c23a 100%);
}

.timeline-tasks {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  min-width: 200px;
}

.task-tag {
  margin: 0;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.overloaded {
  background-color: #f56c6c;
}

.legend-color.normal {
  background-color: #e6a23c;
}

.legend-color.idle {
  background-color: #67c23a;
}
</style>
