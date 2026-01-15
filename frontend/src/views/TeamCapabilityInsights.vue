<template>
  <div class="capability-insights-container">
    <Breadcrumb />
    
    <div class="page-header">
      <h2>团队能力洞察</h2>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange" v-loading="loading">
      <!-- 技能矩阵 -->
      <el-tab-pane label="技能矩阵" name="skill-matrix">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Grid /></el-icon>
              <span>团队技能矩阵</span>
            </div>
          </template>
          <div v-if="skillMatrixData.skill_names.length > 0" class="skill-matrix-table">
            <el-table
              :data="skillMatrixTableData"
              border
              stripe
              style="width: 100%"
              :max-height="600"
            >
              <el-table-column prop="developer" label="开发人员" width="150" fixed="left">
                <template #default="{ row }">
                  <div class="developer-cell">
                    <div class="developer-name">{{ row.full_name || row.username }}</div>
                    <div class="developer-sequence" v-if="row.sequence_level">
                      <el-tag size="small" type="info">{{ row.sequence_level }}</el-tag>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                v-for="skill in skillMatrixData.skill_names"
                :key="skill"
                :label="skill"
                width="100"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag
                    v-if="row.skills[skill]"
                    :type="getProficiencyType(row.skills[skill])"
                    size="small"
                  >
                    {{ getProficiencyText(row.skills[skill]) }}
                  </el-tag>
                  <span v-else class="no-skill">-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无技能数据" :image-size="100" />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 人才梯队 -->
      <el-tab-pane label="人才梯队" name="talent-ladder">
        <el-row :gutter="20">
          <!-- 梯队概览 -->
          <el-col :span="24">
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><UserFilled /></el-icon>
                  <span>梯队概览</span>
                </div>
              </template>
              <div v-if="talentLadderData.ladder_summary.length > 0">
                <WorkloadChart
                  type="bar"
                  :data="ladderSummaryChartData"
                  title=""
                  series-name="人数"
                  height="300px"
                />
              </div>
              <div v-else class="empty-state">
                <el-empty description="暂无梯队数据" :image-size="100" />
              </div>
            </el-card>
          </el-col>

          <!-- 各梯队详情 -->
          <el-col
            v-for="(members, level) in talentLadderData.ladder_data"
            :key="level"
            :span="12"
            style="margin-top: 20px"
          >
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><User /></el-icon>
                  <span>{{ level }} ({{ members.length }}人)</span>
                </div>
              </template>
              <el-table :data="members" stripe style="width: 100%">
                <el-table-column prop="full_name" label="姓名" width="120">
                  <template #default="{ row }">
                    {{ row.full_name || row.username }}
                  </template>
                </el-table-column>
                <el-table-column prop="total_skills" label="技能总数" width="100" align="center" />
                <el-table-column label="技能分布" width="200">
                  <template #default="{ row }">
                    <div class="skill-distribution">
                      <el-tag size="small" type="danger">精通: {{ row.expert_skills }}</el-tag>
                      <el-tag size="small" type="warning">熟练: {{ row.proficient_skills }}</el-tag>
                      <el-tag size="small" type="info">熟悉: {{ row.familiar_skills }}</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="total_man_days" label="工作量(人天)" width="120" align="center">
                  <template #default="{ row }">
                    {{ row.total_man_days.toFixed(1) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 能力分布 -->
      <el-tab-pane label="能力分布" name="distribution">
        <el-row :gutter="20">
          <!-- 熟练度分布 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>技能熟练度分布</span>
                </div>
              </template>
              <WorkloadChart
                v-if="capabilityDistributionData.proficiency_distribution"
                type="pie"
                :data="proficiencyChartData"
                title=""
                series-name="技能数"
                height="300px"
              />
            </el-card>
          </el-col>

          <!-- 序列等级分布 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><UserFilled /></el-icon>
                  <span>序列等级分布</span>
                </div>
              </template>
              <WorkloadChart
                v-if="capabilityDistributionData.sequence_distribution"
                type="pie"
                :data="sequenceChartData"
                title=""
                series-name="人数"
                height="300px"
              />
            </el-card>
          </el-col>

          <!-- 技能数量分布 -->
          <el-col :span="12" style="margin-top: 20px">
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><List /></el-icon>
                  <span>技能数量分布</span>
                </div>
              </template>
              <WorkloadChart
                v-if="capabilityDistributionData.skill_count_distribution"
                type="bar"
                :data="skillCountChartData"
                title=""
                series-name="人数"
                height="300px"
              />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Grid,
  UserFilled,
  User,
  DataAnalysis,
  List,
} from '@element-plus/icons-vue'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import WorkloadChart from '@/components/business/WorkloadChart.vue'
import {
  getSkillMatrix,
  getTalentLadder,
  getCapabilityDistribution,
  type SkillMatrixResponse,
  type TalentLadderResponse,
  type CapabilityDistributionResponse,
} from '@/api/capability'

const loading = ref(false)
const activeTab = ref('skill-matrix')

const skillMatrixData = ref<SkillMatrixResponse>({
  skill_names: [],
  developers: [],
})

const talentLadderData = ref<TalentLadderResponse>({
  ladder_summary: [],
  ladder_data: {},
})

const capabilityDistributionData = ref<CapabilityDistributionResponse>({
  proficiency_distribution: { expert: 0, proficient: 0, familiar: 0 },
  sequence_distribution: {},
  skill_count_distribution: { '0-5': 0, '6-10': 0, '11-15': 0, '16+': 0 },
  total_members: 0,
})

// 技能矩阵表格数据
const skillMatrixTableData = computed(() => {
  return skillMatrixData.value.developers.map(dev => ({
    ...dev,
    skills: dev.skills || {},
  }))
})

// 梯队概览图表数据
const ladderSummaryChartData = computed(() => {
  return talentLadderData.value.ladder_summary.map(item => ({
    name: item.level,
    value: item.count,
  }))
})

// 熟练度分布图表数据
const proficiencyChartData = computed(() => {
  const dist = capabilityDistributionData.value.proficiency_distribution
  return [
    { name: '精通', value: dist.expert },
    { name: '熟练', value: dist.proficient },
    { name: '熟悉', value: dist.familiar },
  ]
})

// 序列等级分布图表数据
const sequenceChartData = computed(() => {
  return Object.entries(capabilityDistributionData.value.sequence_distribution).map(
    ([level, count]) => ({
      name: level,
      value: count,
    })
  )
})

// 技能数量分布图表数据
const skillCountChartData = computed(() => {
  const dist = capabilityDistributionData.value.skill_count_distribution
  return [
    { name: '0-5个', value: dist['0-5'] },
    { name: '6-10个', value: dist['6-10'] },
    { name: '11-15个', value: dist['11-15'] },
    { name: '16+个', value: dist['16+'] },
  ]
})

// 获取熟练度类型
const getProficiencyType = (proficiency: string) => {
  const typeMap: Record<string, string> = {
    expert: 'danger',
    proficient: 'warning',
    familiar: 'info',
  }
  return typeMap[proficiency] || 'info'
}

// 获取熟练度文本
const getProficiencyText = (proficiency: string) => {
  const textMap: Record<string, string> = {
    expert: '精通',
    proficient: '熟练',
    familiar: '熟悉',
  }
  return textMap[proficiency] || proficiency
}

// 加载数据
const loadSkillMatrix = async () => {
  try {
    const data = await getSkillMatrix()
    skillMatrixData.value = data
  } catch (error: any) {
    console.error('加载技能矩阵失败:', error)
    ElMessage.error('加载技能矩阵失败')
  }
}

const loadTalentLadder = async () => {
  try {
    const data = await getTalentLadder()
    talentLadderData.value = data
  } catch (error: any) {
    console.error('加载人才梯队失败:', error)
    ElMessage.error('加载人才梯队失败')
  }
}

const loadCapabilityDistribution = async () => {
  try {
    const data = await getCapabilityDistribution()
    capabilityDistributionData.value = data
  } catch (error: any) {
    console.error('加载能力分布失败:', error)
    ElMessage.error('加载能力分布失败')
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'skill-matrix') {
      await loadSkillMatrix()
    } else if (activeTab.value === 'talent-ladder') {
      await loadTalentLadder()
    } else if (activeTab.value === 'distribution') {
      await loadCapabilityDistribution()
    }
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tabName: string) => {
  refreshData()
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.capability-insights-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.skill-matrix-table {
  overflow-x: auto;
}

.developer-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.developer-name {
  font-weight: bold;
}

.developer-sequence {
  margin-top: 4px;
}

.no-skill {
  color: #ccc;
}

.skill-distribution {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.empty-state {
  padding: 40px;
  text-align: center;
}
</style>
