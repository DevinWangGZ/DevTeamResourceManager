<template>
  <div class="team-workload-board">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>团队负荷看板</span>
          <div class="header-actions">
            <el-select
              v-model="statusFilter"
              placeholder="筛选负荷状态"
              clearable
              size="small"
              style="width: 150px; margin-right: 10px;"
              @change="handleFilterChange"
            >
              <el-option label="全部" value="" />
              <el-option label="过载" value="overloaded" />
              <el-option label="正常" value="normal" />
              <el-option label="空闲" value="idle" />
            </el-select>
            <el-button size="small" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="workload-board-content">
        <!-- 统计概览 -->
        <div class="statistics-overview">
          <div class="stat-item">
            <div class="stat-label">总成员数</div>
            <div class="stat-value">{{ totalMembers }}</div>
          </div>
          <div class="stat-item overloaded">
            <div class="stat-label">过载成员</div>
            <div class="stat-value">{{ overloadedCount }}</div>
          </div>
          <div class="stat-item normal">
            <div class="stat-label">正常成员</div>
            <div class="stat-value">{{ normalCount }}</div>
          </div>
          <div class="stat-item idle">
            <div class="stat-label">空闲成员</div>
            <div class="stat-value">{{ idleCount }}</div>
          </div>
        </div>

        <!-- 成员负荷卡片列表 -->
        <div class="members-grid">
          <div
            v-for="member in filteredMembers"
            :key="member.user_id"
            class="member-card"
            :class="`status-${member.workload_status}`"
            @click="viewMemberDetail(member)"
          >
            <div class="member-header">
              <div class="member-info">
                <div class="member-name">{{ member.full_name || member.username }}</div>
                <div class="member-username">@{{ member.username }}</div>
              </div>
              <el-tag
                :type="getWorkloadStatusType(member.workload_status)"
                :effect="member.workload_status === 'overloaded' ? 'dark' : 'plain'"
                size="small"
              >
                <el-icon v-if="member.workload_status === 'overloaded'" style="margin-right: 4px;">
                  <WarningFilled />
                </el-icon>
                {{ getWorkloadStatusText(member.workload_status) }}
              </el-tag>
            </div>

            <div class="member-metrics">
              <div class="metric-item">
                <div class="metric-label">投入人天</div>
                <div class="metric-value">{{ parseFloat(member.total_man_days.toString()).toFixed(1) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">进行中任务</div>
                <div class="metric-value">{{ member.active_tasks }}</div>
              </div>
            </div>

            <!-- 负荷进度条 -->
            <div class="workload-progress">
              <div class="progress-label">负荷率</div>
              <el-progress
                :percentage="getWorkloadPercentage(member)"
                :color="getWorkloadProgressColor(member.workload_status)"
                :stroke-width="8"
                :show-text="false"
              />
              <div class="progress-text">{{ getWorkloadPercentage(member) }}%</div>
            </div>
          </div>
        </div>

        <div v-if="filteredMembers.length === 0" class="empty-state">
          <el-empty description="暂无成员数据" :image-size="100" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  Refresh,
  WarningFilled,
} from '@element-plus/icons-vue'
import { getTeamDashboard, type TeamDashboard } from '@/api/dashboard'

interface Props {
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: false,
  refreshInterval: 60000, // 默认60秒
})

const router = useRouter()
const loading = ref(false)
const statusFilter = ref<string>('')
const dashboardData = ref<TeamDashboard | null>(null)

// 计算统计数据
const totalMembers = computed(() => dashboardData.value?.member_summaries?.length || 0)
const overloadedCount = computed(() => 
  dashboardData.value?.member_summaries?.filter(m => m.workload_status === 'overloaded').length || 0
)
const normalCount = computed(() => 
  dashboardData.value?.member_summaries?.filter(m => m.workload_status === 'normal').length || 0
)
const idleCount = computed(() => 
  dashboardData.value?.member_summaries?.filter(m => m.workload_status === 'idle').length || 0
)

// 筛选后的成员列表
const filteredMembers = computed(() => {
  if (!dashboardData.value?.member_summaries) return []
  if (!statusFilter.value) return dashboardData.value.member_summaries
  return dashboardData.value.member_summaries.filter(
    m => m.workload_status === statusFilter.value
  )
})

// 获取负荷状态文本
const getWorkloadStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    overloaded: '过载',
    normal: '正常',
    idle: '空闲',
  }
  return statusMap[status] || status
}

// 获取负荷状态类型
const getWorkloadStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    overloaded: 'danger',
    normal: 'success',
    idle: 'info',
  }
  return typeMap[status] || ''
}

// 计算负荷百分比（基于投入人天，假设每月标准为20人天）
const getWorkloadPercentage = (member: any) => {
  const monthlyStandard = 20 // 每月标准工作量
  const currentWorkload = parseFloat(member.total_man_days.toString())
  const percentage = Math.min((currentWorkload / monthlyStandard) * 100, 150) // 最多显示150%
  return Math.round(percentage)
}

// 获取进度条颜色
const getWorkloadProgressColor = (status: string) => {
  const colorMap: Record<string, string> = {
    overloaded: '#f56c6c',
    normal: '#e6a23c',
    idle: '#67c23a',
  }
  return colorMap[status] || '#409eff'
}

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    const data = await getTeamDashboard()
    dashboardData.value = data
  } catch (error: any) {
    console.error('加载团队负荷数据失败:', error)
    ElMessage.error('加载团队负荷数据失败')
  } finally {
    loading.value = false
  }
}

// 筛选变化处理
const handleFilterChange = () => {
  // 筛选逻辑已在 computed 中处理
}

// 查看成员详情
const viewMemberDetail = (member: any) => {
  // 可以跳转到成员详情页面或显示详细信息
  ElMessage.info(`查看 ${member.full_name || member.username} 的详细信息`)
  // router.push(`/users/${member.user_id}`)
}

// 自动刷新定时器
let refreshTimer: number | null = null

onMounted(() => {
  refreshData()
  
  if (props.autoRefresh) {
    refreshTimer = window.setInterval(() => {
      refreshData()
    }, props.refreshInterval)
  }
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.team-workload-board {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.workload-board-content {
  padding: 20px 0;
}

.statistics-overview {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-item {
  flex: 1;
  text-align: center;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-item.overloaded {
  border-left: 4px solid #f56c6c;
}

.stat-item.normal {
  border-left: 4px solid #e6a23c;
}

.stat-item.idle {
  border-left: 4px solid #67c23a;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.members-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.member-card {
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.3s;
}

.member-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.member-card.status-overloaded {
  border-color: #f56c6c;
  background-color: #fef0f0;
}

.member-card.status-normal {
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

.member-card.status-idle {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.member-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.member-username {
  font-size: 12px;
  color: #999;
}

.member-metrics {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  padding: 15px;
  background-color: #fafafa;
  border-radius: 6px;
}

.metric-item {
  flex: 1;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.workload-progress {
  margin-top: 15px;
}

.progress-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.progress-text {
  text-align: right;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.empty-state {
  padding: 40px;
  text-align: center;
}
</style>
