<template>
  <div class="project-progress-container">
    <Breadcrumb />
    
    <div class="page-header">
      <div class="header-left">
        <h2>{{ projectName || '项目进展数据' }}</h2>
        <el-tag v-if="projectId" type="info">项目ID: {{ projectId }}</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-loading="loading" v-if="progressData">
      <!-- 项目概览卡片 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-item">
              <div class="summary-label">任务完成率</div>
              <el-progress
                type="dashboard"
                :percentage="Math.round(progressData.task_statistics.completion_rate)"
                :color="getCompletionRateColor(progressData.task_statistics.completion_rate)"
              >
                <template #default="{ percentage }">
                  <span class="percentage-value">{{ percentage }}%</span>
                </template>
              </el-progress>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-item">
              <div class="summary-label">产值完成率</div>
              <el-progress
                type="dashboard"
                :percentage="Math.round(progressData.output_statistics.completion_rate)"
                :color="getCompletionRateColor(progressData.output_statistics.completion_rate)"
              >
                <template #default="{ percentage }">
                  <span class="percentage-value">{{ percentage }}%</span>
                </template>
              </el-progress>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-item">
              <div class="summary-label">总任务数</div>
              <div class="summary-value">{{ progressData.task_statistics.total }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">已完成</div>
              <div class="summary-value text-success">{{ progressData.task_statistics.confirmed }}</div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-item">
              <div class="summary-label">项目持续时间</div>
              <div class="summary-value">{{ progressData.project_duration_days }} 天</div>
            </div>
            <div class="summary-item" v-if="progressData.project_start_date">
              <div class="summary-label">开始时间</div>
              <div class="summary-value-small">{{ formatDate(progressData.project_start_date) }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 任务完成情况图表 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>任务状态分布</span>
            </template>
            <WorkloadChart
              type="pie"
              :data="taskStatusChartData"
              title=""
              height="300px"
              series-name="任务数"
            />
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card>
            <template #header>
              <span>月度任务完成趋势</span>
            </template>
            <WorkloadChart
              type="line"
              :data="monthlyChartData"
              title=""
              height="300px"
              series-name="已完成任务"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 工作量统计 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>工作量统计</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">总拟投入人天</div>
              <div class="stat-value">{{ progressData.workload_statistics.total_estimated_man_days.toFixed(2) }} 人天</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">总实际投入人天</div>
              <div class="stat-value text-primary">{{ progressData.workload_statistics.total_actual_man_days.toFixed(2) }} 人天</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 产值数据 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <div class="card-header">
            <span>产值数据</span>
            <el-tag v-if="progressData.output_statistics.is_over_budget" type="danger">
              超出预算
            </el-tag>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">预计产值</div>
              <div class="stat-value">¥{{ formatMoney(progressData.output_statistics.estimated_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">任务产值</div>
              <div class="stat-value">¥{{ formatMoney(progressData.output_statistics.task_output_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">已分配产值</div>
              <div class="stat-value text-success">¥{{ formatMoney(progressData.output_statistics.allocated_output_value) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-label">产值完成率</div>
              <el-progress
                :percentage="Math.round(progressData.output_statistics.completion_rate)"
                :color="getCompletionRateColor(progressData.output_statistics.completion_rate)"
              />
            </div>
          </el-col>
        </el-row>
        <el-alert
          v-if="progressData.output_statistics.is_over_budget"
          type="warning"
          :closable="false"
          style="margin-top: 20px"
        >
          <template #title>
            <strong>产值超出预算提醒</strong>
          </template>
          <div>
            当前任务产值（¥{{ formatMoney(progressData.output_statistics.task_output_value) }}）已超出预计产值（¥{{ formatMoney(progressData.output_statistics.estimated_value) }}）。
            <br />
            建议：找业主补充合同或找部门申请产值补贴。
          </div>
        </el-alert>
      </el-card>

      <!-- 任务状态详细统计 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>任务状态详细统计</span>
        </template>
        <el-table :data="taskStatusTableData" stripe>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ row.statusText }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="任务数" width="120" />
          <el-table-column prop="percentage" label="占比" width="150">
            <template #default="{ row }">
              <el-progress :percentage="row.percentage" :show-text="true" />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import { getProjectProgress, type ProjectProgressResponse } from '@/api/project'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const projectId = ref<number | null>(null)
const projectName = ref<string>('')
const progressData = ref<ProjectProgressResponse | null>(null)

// 任务状态分布图表数据
const taskStatusChartData = computed(() => {
  if (!progressData.value) return []
  const stats = progressData.value.task_statistics
  return [
    { name: '已完成', value: stats.confirmed },
    { name: '进行中', value: stats.in_progress },
    { name: '已认领', value: stats.claimed },
    { name: '已提交', value: stats.submitted },
    { name: '已发布', value: stats.published },
    { name: '草稿', value: stats.draft },
  ].filter(item => item.value > 0)
})

// 月度任务完成趋势图表数据
const monthlyChartData = computed(() => {
  if (!progressData.value) return []
  return progressData.value.monthly_statistics.map(item => ({
    name: item.month,
    value: item.confirmed_tasks,
  }))
})

// 任务状态详细统计表格数据
const taskStatusTableData = computed(() => {
  if (!progressData.value) return []
  const stats = progressData.value.task_statistics
  const total = stats.total
  if (total === 0) return []

  const statusMap = [
    { status: 'confirmed', statusText: '已完成', count: stats.confirmed },
    { status: 'in_progress', statusText: '进行中', count: stats.in_progress },
    { status: 'claimed', statusText: '已认领', count: stats.claimed },
    { status: 'submitted', statusText: '已提交', count: stats.submitted },
    { status: 'published', statusText: '已发布', count: stats.published },
    { status: 'draft', statusText: '草稿', count: stats.draft },
    { status: 'archived', statusText: '已归档', count: stats.archived },
  ]

  return statusMap.map(item => ({
    ...item,
    percentage: total > 0 ? Math.round((item.count / total) * 100) : 0,
  }))
})

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    published: 'success',
    claimed: 'primary',
    in_progress: 'primary',
    submitted: 'warning',
    confirmed: 'success',
    archived: 'info',
  }
  return typeMap[status] || ''
}

const getCompletionRateColor = (rate: number) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

const loadProgress = async () => {
  if (!projectId.value) return

  loading.value = true
  try {
    const data = await getProjectProgress(projectId.value)
    progressData.value = data
    projectName.value = data.project_name
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载项目进展数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadProgress()
}

const goBack = () => {
  router.push('/projects')
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    projectId.value = Number(id)
    loadProgress()
  } else {
    ElMessage.error('项目ID无效')
    router.push('/projects')
  }
})
</script>

<style scoped>
.project-progress-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
}

.header-right {
  display: flex;
  gap: 10px;
}

.summary-card {
  height: 100%;
}

.summary-item {
  text-align: center;
  padding: 10px 0;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

.summary-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.summary-value-small {
  font-size: 14px;
  color: #666;
}

.percentage-value {
  font-size: 18px;
  font-weight: bold;
}

.text-success {
  color: #67c23a;
}

.text-primary {
  color: #409eff;
}

.stat-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
