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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
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
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    
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

    statisticList.value = statisticsResult.items
    total.value = statisticsResult.total
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
</style>
