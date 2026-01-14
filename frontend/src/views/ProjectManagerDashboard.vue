<template>
  <div class="dashboard-container">
    <Breadcrumb />
    
    <div class="dashboard-header">
      <h2>项目仪表盘</h2>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- 待确认任务卡片 -->
      <el-col :span="6">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>待确认任务</span>
            </div>
          </template>
          <div class="summary-content">
            <div class="summary-item">
              <div class="summary-value text-warning" style="font-size: 36px;">
                {{ dashboardData?.pending_confirmation_count || 0 }}
              </div>
              <div class="summary-label">个任务等待确认</div>
            </div>
            <el-button 
              type="warning" 
              style="width: 100%; margin-top: 15px;"
              @click="goToPendingTasks"
              v-if="dashboardData?.pending_confirmation_count > 0"
            >
              立即处理
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 项目统计卡片 -->
      <el-col :span="18">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><FolderOpened /></el-icon>
              <span>项目概览</span>
            </div>
          </template>
          <div class="project-overview">
            <div class="overview-item" v-for="summary in dashboardData?.project_summaries || []" :key="summary.project_id">
              <div class="project-name">{{ summary.project_name }}</div>
              <div class="project-stats">
                <el-tag type="info">总任务: {{ summary.total_tasks }}</el-tag>
                <el-tag type="success">已完成: {{ summary.completed_tasks }}</el-tag>
                <el-tag type="primary">进行中: {{ summary.in_progress_tasks }}</el-tag>
                <el-tag type="warning" v-if="summary.pending_confirmation > 0">
                  待确认: {{ summary.pending_confirmation }}
                </el-tag>
              </div>
            </div>
            <div v-if="!dashboardData?.project_summaries || dashboardData.project_summaries.length === 0" class="empty-state">
              <el-empty description="暂无项目" :image-size="80" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目进度和任务完成情况图表 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><FolderOpened /></el-icon>
              <span>项目任务完成情况</span>
            </div>
          </template>
          <WorkloadChart
            v-if="dashboardData?.project_summaries && dashboardData.project_summaries.length > 0"
            type="bar"
            :data="projectTaskChartData"
            title=""
            height="300px"
            series-name="已完成任务"
          />
          <div v-else class="empty-state">
            <el-empty description="暂无项目数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><Money /></el-icon>
              <span>项目产值对比</span>
            </div>
          </template>
          <WorkloadChart
            v-if="dashboardData?.output_summaries && dashboardData.output_summaries.length > 0"
            type="bar"
            :data="projectOutputChartData"
            title=""
            height="300px"
            series-name="已分配产值"
          />
          <div v-else class="empty-state">
            <el-empty description="暂无产值数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目产值汇总 -->
    <el-card class="output-card" style="margin-top: 20px" v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-icon><Money /></el-icon>
          <span>项目产值汇总</span>
        </div>
      </template>
      <el-table
        :data="dashboardData?.output_summaries || []"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="project_name" label="项目名称" />
        <el-table-column prop="estimated_value" label="预计产值" width="150">
          <template #default="{ row }">
            ¥{{ formatMoney(row.estimated_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="task_output_value" label="任务产值" width="150">
          <template #default="{ row }">
            ¥{{ formatMoney(row.task_output_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="allocated_output_value" label="已分配产值" width="150">
          <template #default="{ row }">
            ¥{{ formatMoney(row.allocated_output_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_over_budget" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_over_budget ? 'danger' : 'success'">
              {{ row.is_over_budget ? '超出预算' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="完成率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="getCompletionRate(row)"
              :color="row.is_over_budget ? '#f56c6c' : '#67c23a'"
            />
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!dashboardData?.output_summaries || dashboardData.output_summaries.length === 0" class="empty-state">
        <el-empty description="暂无产值数据" :image-size="100" />
      </div>
    </el-card>

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
        <el-button type="primary" size="large" @click="goToTasks">
          <el-icon><List /></el-icon>
          任务管理
        </el-button>
        <el-button type="success" size="large" @click="goToCreateTask">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
        <el-button type="info" size="large" @click="goToProjects">
          <el-icon><FolderOpened /></el-icon>
          项目管理
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
  Bell,
  FolderOpened,
  Money,
  Operation,
  List,
  Plus,
  Refresh,
} from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import { getProjectManagerDashboard, type ProjectManagerDashboard, type ProjectOutputSummary } from '@/api/dashboard'
import { computed } from 'vue'

const router = useRouter()
const loading = ref(false)
const dashboardData = ref<ProjectManagerDashboard | null>(null)

// 项目任务完成情况图表数据（堆叠柱状图需要特殊处理）
const projectTaskChartData = computed(() => {
  if (!dashboardData.value?.project_summaries) return []
  // 返回已完成任务数用于展示
  return dashboardData.value.project_summaries.map(project => ({
    name: project.project_name,
    value: project.completed_tasks,
  }))
})

// 项目产值对比图表数据
const projectOutputChartData = computed(() => {
  if (!dashboardData.value?.output_summaries) return []
  return dashboardData.value.output_summaries.map(output => ({
    name: output.project_name,
    value: parseFloat(output.allocated_output_value.toString()),
  }))
})

const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

const getCompletionRate = (row: ProjectOutputSummary) => {
  if (!row.estimated_value || row.estimated_value === 0) {
    return 0
  }
  const rate = (row.allocated_output_value / row.estimated_value) * 100
  // 限制在0-100之间，避免显示超过100%
  return Math.min(Math.max(Math.round(rate), 0), 100)
}

const getReminderType = (type: string) => {
  const typeMap: Record<string, string> = {
    pending_confirmation: 'warning',
    over_budget: 'danger',
  }
  return typeMap[type] || 'info'
}

const handleTodoClick = (reminder: { link?: string }) => {
  if (reminder.link) {
    router.push(reminder.link)
  }
}

const goToPendingTasks = () => {
  router.push('/tasks?status=submitted')
}

const goToTasks = () => {
  router.push('/tasks')
}

const goToCreateTask = () => {
  router.push('/tasks')
  // 可以添加一个参数来触发创建对话框
  setTimeout(() => {
    // 这里可以通过事件总线或其他方式触发创建对话框
  }, 100)
}

const goToProjects = () => {
  router.push('/projects')
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const data = await getProjectManagerDashboard()
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
  padding: 10px 0;
  text-align: center;
}

.summary-item {
  margin-bottom: 15px;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.text-warning {
  color: #e6a23c;
}

.project-overview {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.overview-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: box-shadow 0.3s;
}

.overview-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.project-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
}

.project-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
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
