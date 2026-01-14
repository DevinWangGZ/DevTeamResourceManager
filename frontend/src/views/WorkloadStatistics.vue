<template>
  <div class="workload-container">
    <Breadcrumb />
    <el-card>
      <template #header>
        <div class="workload-header">
          <h2>工作量统计</h2>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="项目ID">
          <el-input-number
            v-model="filters.project_id"
            placeholder="项目ID（可选）"
            :min="1"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="filters.period_start"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="filters.period_end"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadStatistics">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 汇总信息 -->
      <el-card shadow="never" class="summary-card" v-if="summary">
        <h3>工作量汇总</h3>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总投入人天</div>
              <div class="summary-value">{{ summary.total_man_days }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">参与项目数</div>
              <div class="summary-value">{{ summary.project_count }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">统计周期</div>
              <div class="summary-value">
                {{ formatDate(summary.period_start) }} ~ {{ formatDate(summary.period_end) }}
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 数据可视化 -->
      <el-row :gutter="20" style="margin-top: 20px" v-if="statisticList.length > 0">
        <!-- 工作量趋势图 -->
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>工作量趋势</span>
                <el-radio-group v-model="trendViewType" size="small" @change="updateTrendChart">
                  <el-radio-button label="month">按月</el-radio-button>
                  <el-radio-button label="project">按项目</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <WorkloadChart
              type="trend"
              :data="trendChartData"
              :x-axis-data="trendXAxisData"
              title=""
              series-name="投入人天"
              height="300px"
            />
          </el-card>
        </el-col>

        <!-- 按项目统计 -->
        <el-col :span="12" style="margin-top: 20px">
          <el-card>
            <template #header>
              <span>按项目统计</span>
            </template>
            <WorkloadChart
              type="bar"
              :data="projectChartData"
              title=""
              series-name="投入人天"
              height="300px"
            />
          </el-card>
        </el-col>

        <!-- 项目占比 -->
        <el-col :span="12" style="margin-top: 20px">
          <el-card>
            <template #header>
              <span>项目占比</span>
            </template>
            <WorkloadChart
              type="pie"
              :data="projectChartData"
              title=""
              series-name="投入人天"
              height="300px"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 统计列表 -->
      <el-table
        :data="statisticList"
        v-loading="loading"
        stripe
        style="margin-top: 20px"
      >
        <el-table-column prop="period_start" label="统计周期" width="200">
          <template #default="{ row }">
            {{ formatDate(row.period_start) }} ~ {{ formatDate(row.period_end) }}
          </template>
        </el-table-column>
        <el-table-column prop="project_id" label="项目ID" width="100" />
        <el-table-column prop="project_name" label="项目名称" width="200">
          <template #default="{ row }">
            {{ row.project_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_man_days" label="投入人天" width="120">
          <template #default="{ row }">
            <el-tag type="success">{{ row.total_man_days }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import {
  getMyWorkloadStatistics,
  getMyWorkloadSummary,
  type WorkloadStatistic,
  type WorkloadSummary,
} from '@/api/workload'

const loading = ref(false)
const statisticList = ref<WorkloadStatistic[]>([])
const summary = ref<WorkloadSummary | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  project_id: undefined as number | undefined,
  period_start: undefined as string | undefined,
  period_end: undefined as string | undefined,
})

const trendViewType = ref<'month' | 'project'>('month')

// 趋势图数据
const trendChartData = computed(() => {
  if (trendViewType.value === 'month') {
    // 按月统计
    const monthMap = new Map<string, number>()
    statisticList.value.forEach((item) => {
      const date = new Date(item.period_start)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const current = monthMap.get(monthKey) || 0
      monthMap.set(monthKey, current + parseFloat(item.total_man_days.toString()))
    })
    return Array.from(monthMap.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([key, value]) => ({
        period_start: key + '-01',
        total_man_days: value,
      }))
  } else {
    // 按项目统计（用于趋势图）
    return statisticList.value
  }
})

const trendXAxisData = computed(() => {
  return trendChartData.value.map((item: any) => {
    if (item.period_start) {
      const date = new Date(item.period_start)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    }
    return item.project_name || ''
  })
})

// 按项目统计图表数据
const projectChartData = computed(() => {
  const projectMap = new Map<string, number>()
  statisticList.value.forEach((item) => {
    const projectName = item.project_name || `项目${item.project_id || '未知'}`
    const current = projectMap.get(projectName) || 0
    projectMap.set(projectName, current + parseFloat(item.total_man_days.toString()))
  })
  return Array.from(projectMap.entries()).map(([name, value]) => ({
    project_name: name,
    total_man_days: value,
  }))
})

const updateTrendChart = () => {
  // 图表会自动更新，因为使用了computed
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadStatistics = async () => {
  loading.value = true
  try {
    const params: any = {}
    
    if (filters.project_id) {
      params.project_id = filters.project_id
    }
    if (filters.period_start) {
      params.period_start = filters.period_start
    }
    if (filters.period_end) {
      params.period_end = filters.period_end
    }

    const [statisticsResult, summaryResult] = await Promise.all([
      getMyWorkloadStatistics(params),
      getMyWorkloadSummary({
        period_start: filters.period_start,
        period_end: filters.period_end,
      }),
    ])

    // 客户端分页
    const allItems = statisticsResult.items
    total.value = allItems.length
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    statisticList.value = allItems.slice(start, end)
    
    summary.value = summaryResult
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载工作量统计失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.project_id = undefined
  filters.period_start = undefined
  filters.period_end = undefined
  currentPage.value = 1
  loadStatistics()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadStatistics()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadStatistics()
}

onMounted(() => {
  // 如果没有设置日期范围，设置默认值（当前月份）
  if (!filters.period_start && !filters.period_end) {
    const today = new Date()
    const year = today.getFullYear()
    const month = today.getMonth()
    filters.period_start = `${year}-${String(month + 1).padStart(2, '0')}-01`
    const lastDay = new Date(year, month + 1, 0).getDate()
    filters.period_end = `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
  }
  loadStatistics()
})
</script>

<style scoped>
.workload-container {
  padding: 20px;
}

.workload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.workload-header h2 {
  margin: 0;
}

.filter-form {
  margin-bottom: 20px;
}

.summary-card {
  margin-bottom: 20px;
}

.summary-card h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
