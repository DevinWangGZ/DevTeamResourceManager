<template>
  <div class="dashboard-container">
    <Breadcrumb />
    
    <div class="dashboard-header">
      <h2>个人工作台</h2>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- 任务汇总卡片 -->
      <el-col :span="6">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>我的任务</span>
            </div>
          </template>
          <div class="summary-content">
            <div class="summary-item">
              <div class="summary-label">总任务数</div>
              <div class="summary-value">{{ dashboardData?.task_summary?.total || 0 }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">进行中</div>
              <div class="summary-value text-primary">{{ dashboardData?.task_summary?.in_progress || 0 }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">已提交</div>
              <div class="summary-value text-warning">{{ dashboardData?.task_summary?.submitted || 0 }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">已确认</div>
              <div class="summary-value text-success">{{ dashboardData?.task_summary?.confirmed || 0 }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">待评估</div>
              <div class="summary-value text-info">{{ dashboardData?.task_summary?.pending_eval || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 工作量汇总卡片 -->
      <el-col :span="6">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>工作量概览</span>
            </div>
          </template>
          <div class="summary-content" v-if="dashboardData?.workload_summary">
            <div class="summary-item">
              <div class="summary-label">总投入人天</div>
              <div class="summary-value text-primary">{{ dashboardData.workload_summary.total_man_days }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">参与项目数</div>
              <div class="summary-value">{{ dashboardData.workload_summary.project_count }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">统计周期</div>
              <div class="summary-value-small">
                {{ formatDate(dashboardData.workload_summary.period_start) }} ~ 
                {{ formatDate(dashboardData.workload_summary.period_end) }}
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无工作量数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>

      <!-- 待办提醒卡片 -->
      <el-col :span="12">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>待办提醒</span>
            </div>
          </template>
          <div class="todo-list" v-if="dashboardData?.todo_reminders && dashboardData.todo_reminders.length > 0">
            <div
              v-for="reminder in dashboardData.todo_reminders"
              :key="reminder.type"
              class="todo-item"
              @click="handleTodoClick(reminder)"
            >
              <el-badge :value="reminder.count" class="todo-badge">
                <el-tag :type="getReminderType(reminder.type)" class="todo-tag">
                  {{ reminder.title }}
                </el-tag>
              </el-badge>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无待办事项" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近任务 -->
    <el-card class="recent-tasks-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>最近任务</span>
          <el-button link type="primary" @click="goToTasks" style="margin-left: auto">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table
        :data="dashboardData?.recent_tasks || []"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="title" label="任务标题" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_man_days" label="拟投入人天" width="120">
          <template #default="{ row }">
            {{ row.estimated_man_days || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="actual_man_days" label="实际投入人天" width="130">
          <template #default="{ row }">
            {{ row.actual_man_days || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewTask(row.id)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!dashboardData?.recent_tasks || dashboardData.recent_tasks.length === 0" class="empty-state">
        <el-empty description="暂无任务" :image-size="100" />
      </div>
    </el-card>

    <!-- 任务统计图表 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>任务状态分布</span>
            </div>
          </template>
          <WorkloadChart
            v-if="dashboardData?.task_summary"
            type="pie"
            :data="taskStatusChartData"
            title=""
            height="300px"
            series-name="任务数"
          />
        </el-card>
      </el-col>

      <!-- 工作量概览图表 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>工作量趋势</span>
            </div>
          </template>
          <div v-if="workloadTrendData.length > 0">
            <WorkloadChart
              type="line"
              :data="workloadTrendData"
              title=""
              height="300px"
              series-name="投入人天"
            />
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无工作量趋势数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 工作负荷可视化 -->
    <el-card class="workload-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>工作负荷</span>
        </div>
      </template>
      <WorkloadTimeline title="" />
    </el-card>

    <!-- 快速操作 -->
    <el-card class="quick-actions-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><Operation /></el-icon>
          <span>快速操作</span>
        </div>
      </template>
      <div class="quick-actions">
        <el-button type="success" size="large" @click="goToMarketplace">
          <el-icon><ShoppingBag /></el-icon>
          任务集市
        </el-button>
        <el-button type="primary" size="large" @click="goToTasks">
          <el-icon><List /></el-icon>
          任务管理
        </el-button>
        <el-button type="info" size="large" @click="goToProfile">
          <el-icon><User /></el-icon>
          个人档案
        </el-button>
        <el-button type="warning" size="large" @click="goToWorkload">
          <el-icon><DataAnalysis /></el-icon>
          工作量统计
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  List,
  DataAnalysis,
  Bell,
  Clock,
  ArrowRight,
  Operation,
  User,
  ShoppingBag,
} from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadTimeline from '@/components/business/WorkloadTimeline.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import { getDeveloperDashboard, type DeveloperDashboard } from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const dashboardData = ref<DeveloperDashboard | null>(null)

// 任务状态分布图表数据
const taskStatusChartData = computed(() => {
  if (!dashboardData.value?.task_summary) return []
  const summary = dashboardData.value.task_summary
  return [
    { name: '进行中', value: summary.in_progress },
    { name: '已提交', value: summary.submitted },
    { name: '已确认', value: summary.confirmed },
    { name: '待评估', value: summary.pending_eval },
  ].filter(item => item.value > 0)
})

// 工作量趋势数据（模拟数据，实际应从API获取）
const workloadTrendData = computed(() => {
  // TODO: 从API获取工作量趋势数据
  // 目前返回空数组，后续需要添加API接口
  return []
})

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
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
    claimed: 'primary',
    in_progress: 'primary',
    submitted: 'warning',
    confirmed: 'success',
    archived: 'info',
  }
  return typeMap[status] || ''
}

const getReminderType = (type: string) => {
  const typeMap: Record<string, string> = {
    pending_eval: 'warning',
    submitted: 'info',
    upcoming_deadline: 'danger',
  }
  return typeMap[type] || 'info'
}

const handleTodoClick = (reminder: { link?: string }) => {
  if (reminder.link) {
    router.push(reminder.link)
  }
}

const viewTask = (taskId: number) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

const goToTasks = () => {
  router.push('/tasks')
}

const goToProfile = () => {
  router.push('/profile')
}

const goToWorkload = () => {
  router.push('/workload')
}

const goToMarketplace = () => {
  router.push('/marketplace')
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const data = await getDeveloperDashboard()
    dashboardData.value = data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载工作台数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadDashboard()
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.summary-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.summary-content {
  padding: 10px 0;
}

.summary-item {
  margin-bottom: 15px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.summary-value-small {
  font-size: 14px;
  color: #666;
}

.text-primary {
  color: #409eff;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-info {
  color: #909399;
}

.empty-state {
  padding: 20px;
  text-align: center;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.todo-item {
  cursor: pointer;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.todo-item:hover {
  background-color: #f5f7fa;
}

.todo-badge {
  width: 100%;
}

.todo-tag {
  width: 100%;
  padding: 8px 12px;
}

.recent-tasks-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 150px;
}

.chart-card {
  height: 100%;
}
</style>
