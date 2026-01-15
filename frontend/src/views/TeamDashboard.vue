<template>
  <div class="dashboard-container">
    <Breadcrumb />
    
    <div class="dashboard-header">
      <h2>团队管理仪表盘</h2>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- 团队总览卡片 -->
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><UserFilled /></el-icon>
              <span>团队成员</span>
            </div>
          </template>
          <div class="summary-content">
            <div class="summary-value" style="font-size: 48px;">
              {{ dashboardData?.total_members || 0 }}
            </div>
            <div class="summary-label">人</div>
          </div>
        </el-card>
      </el-col>

      <!-- 总工作量卡片 -->
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>团队总工作量</span>
            </div>
          </template>
          <div class="summary-content">
            <div class="summary-value text-primary" style="font-size: 36px;">
              {{ dashboardData?.total_workload || 0 }}
            </div>
            <div class="summary-label">人天</div>
          </div>
        </el-card>
      </el-col>

      <!-- 任务完成率卡片 -->
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><CircleCheckFilled /></el-icon>
              <span>任务完成率</span>
            </div>
          </template>
          <div class="summary-content">
            <el-progress
              type="dashboard"
              :percentage="Math.round(dashboardData?.task_completion_rate || 0)"
              :color="getCompletionRateColor(dashboardData?.task_completion_rate || 0)"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 团队成员汇总 -->
    <el-card class="members-card" style="margin-top: 20px" v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-icon><UserFilled /></el-icon>
          <span>团队成员汇总</span>
        </div>
      </template>
      <el-table
        :data="dashboardData?.member_summaries || []"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="full_name" label="姓名" width="150">
          <template #default="{ row }">
            {{ row.full_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="workload_status" label="负荷状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getWorkloadStatusType(row.workload_status)" :effect="row.workload_status === 'overloaded' ? 'dark' : 'plain'">
              <el-icon v-if="row.workload_status === 'overloaded'" style="margin-right: 4px;"><WarningFilled /></el-icon>
              {{ getWorkloadStatusText(row.workload_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_man_days" label="总投入人天" width="150">
          <template #default="{ row }">
            {{ row.total_man_days }}
          </template>
        </el-table-column>
        <el-table-column prop="active_tasks" label="进行中任务" width="150">
          <template #default="{ row }">
            <el-tag type="primary">{{ row.active_tasks }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewMemberDetail(row.user_id)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!dashboardData?.member_summaries || dashboardData.member_summaries.length === 0" class="empty-state">
        <el-empty description="暂无团队成员数据" :image-size="100" />
      </div>
    </el-card>

    <!-- 团队负荷可视化 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>团队负荷分布</span>
            </div>
          </template>
          <div v-if="dashboardData?.member_summaries && dashboardData.member_summaries.length > 0">
            <WorkloadChart
              type="bar"
              :data="teamWorkloadChartData"
              title=""
              series-name="投入人天"
              height="300px"
            />
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无团队负荷数据" :image-size="100" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><UserFilled /></el-icon>
              <span>团队成员负荷状态</span>
            </div>
          </template>
          <div v-if="dashboardData?.member_summaries && dashboardData.member_summaries.length > 0">
            <WorkloadChart
              type="pie"
              :data="workloadStatusChartData"
              title=""
              series-name="人数"
              height="300px"
            />
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无负荷状态数据" :image-size="100" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 团队负荷看板 -->
    <TeamWorkloadBoard style="margin-top: 20px" />

    <!-- 待办提醒 -->
    <el-card class="todo-card" style="margin-top: 20px" v-loading="loading">
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

    <!-- 快速操作 -->
    <el-card class="quick-actions-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <el-icon><Operation /></el-icon>
          <span>快速操作</span>
        </div>
      </template>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="goToWorkload">
          <el-icon><DataAnalysis /></el-icon>
          团队负荷
        </el-button>
        <el-button type="success" size="large" @click="goToMembers">
          <el-icon><UserFilled /></el-icon>
          人员信息
        </el-button>
        <el-button type="info" size="large" @click="goToPerformance">
          <el-icon><TrendCharts /></el-icon>
          绩效数据
        </el-button>
        <el-button type="warning" size="large" @click="goToCapabilityInsights">
          <el-icon><DataAnalysis /></el-icon>
          能力洞察
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
  UserFilled,
  DataAnalysis,
  CircleCheck,
  Bell,
  Operation,
  Refresh,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import TeamWorkloadBoard from '@/components/business/TeamWorkloadBoard.vue'
import { getTeamDashboard, type TeamDashboard } from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const dashboardData = ref<TeamDashboard | null>(null)

// 团队负荷图表数据
const teamWorkloadChartData = computed(() => {
  if (!dashboardData.value?.member_summaries) return []
  return dashboardData.value.member_summaries.map((member) => ({
    name: member.full_name || member.username,
    total_man_days: parseFloat(member.total_man_days.toString()),
  }))
})

// 负荷状态分布图表数据
const workloadStatusChartData = computed(() => {
  if (!dashboardData.value?.member_summaries) return []
  const statusCount: Record<string, number> = {}
  dashboardData.value.member_summaries.forEach(member => {
    const status = member.workload_status
    statusCount[status] = (statusCount[status] || 0) + 1
  })
  return Object.entries(statusCount).map(([status, count]) => ({
    name: getWorkloadStatusText(status),
    value: count,
  }))
})

const getCompletionRateColor = (rate: number) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getWorkloadStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    overloaded: '过载',
    normal: '正常',
    idle: '空闲',
  }
  return statusMap[status] || status
}

const getWorkloadStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    overloaded: 'danger',
    normal: 'success',
    idle: 'info',
  }
  return typeMap[status] || ''
}

const getReminderType = (type: string) => {
  const typeMap: Record<string, string> = {
    overloaded_members: 'danger',
    idle_members: 'info',
  }
  return typeMap[type] || 'warning'
}

const handleTodoClick = (reminder: { link?: string }) => {
  if (reminder.link) {
    router.push(reminder.link)
  }
}

const viewMemberDetail = (userId: number) => {
  // 查看成员详情，待实现
  ElMessage.info(`查看成员 ${userId} 的详情（功能待实现）`)
}

const goToWorkload = () => {
  // 团队负荷页面，待实现
  ElMessage.info('团队负荷功能待实现')
}

const goToMembers = () => {
  // 人员信息页面，待实现
  ElMessage.info('人员信息功能待实现')
}

const goToPerformance = () => {
  // 绩效数据页面，待实现
  ElMessage.info('绩效数据功能待实现')
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const data = await getTeamDashboard()
    dashboardData.value = data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载仪表盘数据失败')
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

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h2 {
  margin: 0;
  color: #333;
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
  padding: 20px 0;
  text-align: center;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.text-primary {
  color: #409eff;
}

.percentage-value {
  font-size: 18px;
  font-weight: bold;
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
