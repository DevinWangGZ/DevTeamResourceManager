<template>
  <div class="task-marketplace-container">
    <Breadcrumb />
    
    <div class="page-header">
      <h2>任务集市</h2>
      <div class="header-actions">
        <el-switch
          v-model="showRecommend"
          active-text="推荐任务"
          inactive-text="全部任务"
          @change="handleRecommendChange"
        />
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="项目">
          <el-select
            v-model="filterForm.project_id"
            placeholder="全部项目"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所需技能">
          <el-select
            v-model="filterForm.required_skills"
            placeholder="选择技能"
            clearable
            filterable
            multiple
            style="width: 300px"
          >
            <el-option
              v-for="skill in availableSkills"
              :key="skill"
              :label="skill"
              :value="skill"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索任务标题或描述"
            clearable
            style="width: 250px"
            @keyup.enter="loadTasks"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks" :icon="Search">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <div v-loading="loading" class="tasks-section">
      <div v-if="tasks.length === 0" class="empty-state">
        <el-empty description="暂无任务" :image-size="150">
          <el-button type="primary" @click="resetFilter">重置筛选条件</el-button>
        </el-empty>
      </div>

      <div v-else>
        <!-- 任务统计 -->
        <div class="tasks-summary">
          <span>共找到 <strong>{{ total }}</strong> 个任务</span>
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="card">卡片视图</el-radio-button>
            <el-radio-button label="list">列表视图</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 卡片视图 -->
        <div v-if="viewMode === 'card'" class="tasks-grid">
          <TaskCard
            v-for="task in tasks"
            :key="task.id"
            :task="task"
            @claimed="handleTaskClaimed"
          />
        </div>

        <!-- 列表视图 -->
        <el-table
          v-else
          :data="tasks"
          stripe
          style="width: 100%"
          @row-click="viewTaskDetail"
        >
          <el-table-column prop="title" label="任务标题" min-width="200" />
          <el-table-column prop="project_name" label="项目" width="150">
            <template #default="{ row }">
              {{ row.project_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="creator_name" label="创建者" width="120" />
          <el-table-column prop="estimated_man_days" label="拟投入人天" width="120" />
          <el-table-column prop="required_skills" label="所需技能" min-width="200">
            <template #default="{ row }">
              <el-tag
                v-for="(skill, index) in getSkillsList(row.required_skills)"
                :key="index"
                size="small"
                style="margin-right: 5px"
              >
                {{ skill }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="deadline" label="截止时间" width="120">
            <template #default="{ row }">
              {{ row.deadline ? formatDate(row.deadline) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="handleClaim(row)">
                认领
              </el-button>
              <el-button link type="primary" size="small" @click.stop="viewTaskDetail(row)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="total"
            :page-sizes="[12, 24, 48, 96]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import TaskCard from '@/components/business/TaskCard.vue'
import { getMarketplaceTasks, claimTask, type MarketplaceTask } from '@/api/task'
import { getProjects, type Project } from '@/api/project'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const tasks = ref<MarketplaceTask[]>([])
const total = ref(0)
const projectList = ref<Project[]>([])
const showRecommend = ref(false)
const viewMode = ref<'card' | 'list'>('card')

const filterForm = reactive({
  project_id: undefined as number | undefined,
  required_skills: [] as string[],
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 12,
})

// 获取所有可用技能（从任务中提取）
const availableSkills = computed(() => {
  const skillsSet = new Set<string>()
  tasks.value.forEach(task => {
    if (task.required_skills) {
      task.required_skills.split(',').forEach(skill => {
        const trimmed = skill.trim()
        if (trimmed) skillsSet.add(trimmed)
      })
    }
  })
  return Array.from(skillsSet).sort()
})

const getSkillsList = (skills?: string) => {
  if (!skills) return []
  return skills.split(',').map(s => s.trim()).filter(s => s)
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const loadProjects = async () => {
  try {
    const response = await getProjects({ limit: 1000 })
    projectList.value = response.items
  } catch (error: any) {
    console.error('加载项目列表失败:', error)
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    if (filterForm.project_id) {
      params.project_id = filterForm.project_id
    }

    if (filterForm.keyword) {
      params.keyword = filterForm.keyword
    }

    if (filterForm.required_skills && filterForm.required_skills.length > 0) {
      params.required_skills = filterForm.required_skills.join(',')
    }

    if (showRecommend.value && userStore.userInfo?.role === 'developer') {
      params.recommend = true
    }

    const data = await getMarketplaceTasks(params)
    tasks.value = data.tasks
    total.value = data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载任务失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.project_id = undefined
  filterForm.required_skills = []
  filterForm.keyword = ''
  pagination.page = 1
  loadTasks()
}

const refreshData = () => {
  loadTasks()
}

const handleRecommendChange = () => {
  pagination.page = 1
  loadTasks()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadTasks()
}

const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadTasks()
}

const viewTaskDetail = (task: MarketplaceTask) => {
  router.push({ name: 'TaskDetail', params: { id: task.id } })
}

const handleClaim = async (task: MarketplaceTask) => {
  try {
    await ElMessageBox.confirm('确定要认领此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await claimTask(task.id)
    ElMessage.success('任务认领成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '认领任务失败')
    }
  }
}

const handleTaskClaimed = (taskId: number) => {
  loadTasks()
}

onMounted(() => {
  loadProjects()
  loadTasks()
})
</script>

<style scoped>
.task-marketplace-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.tasks-section {
  margin-top: 20px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.tasks-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px 0;
}

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .tasks-grid {
    grid-template-columns: 1fr;
  }
}
</style>
