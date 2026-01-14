<template>
  <div class="project-task-execution-container">
    <Breadcrumb />
    
    <div class="page-header">
      <div class="header-left">
        <h2>{{ projectName || '项目任务执行视图' }}</h2>
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

    <!-- 筛选条件 -->
    <el-card class="filter-card" style="margin-top: 20px">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="任务状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="待评估" value="pending_eval" />
            <el-option label="已认领" value="claimed" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="认领者">
          <el-select v-model="filterForm.assignee_id" placeholder="全部人员" clearable filterable style="width: 150px">
            <el-option
              v-for="assignee in assigneeList"
              :key="assignee.id"
              :label="assignee.name"
              :value="assignee.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索任务标题或描述"
            clearable
            style="width: 200px"
            @keyup.enter="loadTasks"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 状态统计 -->
    <el-row :gutter="20" style="margin-top: 20px" v-if="statusSummary">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>任务状态统计</span>
          </template>
          <div class="status-summary">
            <el-tag
              v-for="(count, status) in statusSummary"
              :key="status"
              :type="getStatusType(status)"
              size="large"
              class="status-tag"
            >
              {{ getStatusText(status) }}: {{ count }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 视图切换 -->
    <el-card class="view-switch-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>任务视图</span>
          <el-radio-group v-model="viewType" size="small">
            <el-radio-button label="list">列表视图</el-radio-button>
            <el-radio-button label="timeline">时间线视图</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 列表视图 -->
      <div v-if="viewType === 'list'">
        <el-table
          :data="tasks"
          v-loading="loading"
          stripe
          style="width: 100%"
          @row-click="viewTaskDetail"
        >
          <el-table-column prop="title" label="任务标题" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="creator_name" label="创建者" width="120" />
          <el-table-column prop="assignee_name" label="认领者" width="120">
            <template #default="{ row }">
              {{ row.assignee_name || '未认领' }}
            </template>
          </el-table-column>
          <el-table-column prop="estimated_man_days" label="拟投入人天" width="120" />
          <el-table-column prop="actual_man_days" label="实际投入人天" width="130">
            <template #default="{ row }">
              {{ row.actual_man_days || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="排期" width="200">
            <template #default="{ row }">
              <div v-if="row.schedule">
                <div>{{ formatDate(row.schedule.start_date) }} ~ {{ formatDate(row.schedule.end_date) }}</div>
                <el-tag v-if="row.schedule.is_pinned" type="warning" size="small">已置顶</el-tag>
              </div>
              <span v-else class="text-muted">未排期</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="viewTaskDetail(row)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 时间线视图 -->
      <div v-if="viewType === 'timeline'">
        <TaskTimeline :tasks="tasks" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import TaskTimeline from '@/components/business/TaskTimeline.vue'
import { getProjectTasks, type ProjectTaskExecutionResponse, type ProjectTask } from '@/api/project'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const projectId = ref<number | null>(null)
const projectName = ref<string>('')
const tasks = ref<ProjectTask[]>([])
const statusSummary = ref<Record<string, number>>({})
const viewType = ref<'list' | 'timeline'>('list')

const filterForm = reactive({
  status: '',
  assignee_id: undefined as number | undefined,
  keyword: '',
})

// 获取所有认领者列表
const assigneeList = computed(() => {
  const assignees = new Map<number, { id: number; name: string }>()
  tasks.value.forEach(task => {
    if (task.assignee_id && task.assignee_name) {
      assignees.set(task.assignee_id, {
        id: task.assignee_id,
        name: task.assignee_name,
      })
    }
  })
  return Array.from(assignees.values())
})

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

const loadTasks = async () => {
  if (!projectId.value) return

  loading.value = true
  try {
    const params: any = {}
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.assignee_id) params.assignee_id = filterForm.assignee_id
    if (filterForm.keyword) params.keyword = filterForm.keyword

    const data = await getProjectTasks(projectId.value, params)
    tasks.value = data.tasks
    statusSummary.value = data.status_summary
    projectName.value = data.project_name
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载任务数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.assignee_id = undefined
  filterForm.keyword = ''
  loadTasks()
}

const refreshData = () => {
  loadTasks()
}

const viewTaskDetail = (task: ProjectTask) => {
  router.push({ name: 'TaskDetail', params: { id: task.id } })
}

const goBack = () => {
  router.push('/projects')
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    projectId.value = Number(id)
    loadTasks()
  } else {
    ElMessage.error('项目ID无效')
    router.push('/projects')
  }
})
</script>

<style scoped>
.project-task-execution-container {
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

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.status-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.status-tag {
  font-size: 14px;
  padding: 8px 16px;
}

.view-switch-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-muted {
  color: #999;
}
</style>
