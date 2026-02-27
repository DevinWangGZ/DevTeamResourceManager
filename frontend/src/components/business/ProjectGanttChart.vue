<template>
  <div class="project-gantt-chart">
    <!-- 工具栏 -->
    <div class="gantt-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索任务名称"
          clearable
          style="width: 200px"
          :prefix-icon="Search"
        />
        <el-select v-model="filterPriority" placeholder="优先级" clearable style="width: 120px">
          <el-option label="P0 最紧急" value="P0" />
          <el-option label="P1 较紧急" value="P1" />
          <el-option label="P2 常规" value="P2" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
          <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-checkbox v-model="groupByAssignee">按负责人分组</el-checkbox>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="emit('refresh')">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 无数据 -->
    <el-empty v-if="!loading && filteredTasks.length === 0" description="暂无排期数据" />

    <!-- 甘特图容器 -->
    <div
      v-show="filteredTasks.length > 0"
      ref="chartRef"
      class="gantt-container"
      v-loading="loading"
    />

    <!-- 图例 -->
    <div class="gantt-legend">
      <span class="legend-item"><span class="legend-bar" style="background:#409EFF"></span>进行中/已认领</span>
      <span class="legend-item"><span class="legend-bar" style="background:#67C23A"></span>已完成</span>
      <span class="legend-item"><span class="legend-bar" style="background:#F56C6C"></span>延误</span>
      <span class="legend-item"><span class="legend-bar" style="background:#E6A23C"></span>已提交</span>
      <span class="legend-item"><span class="legend-bar legend-dashed"></span>未排期（已发布）</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import type { ProjectScheduleTask } from '@/api/task'
import * as echarts from 'echarts'

const props = defineProps<{
  tasks: ProjectScheduleTask[]
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const keyword = ref('')
const filterPriority = ref('')
const filterStatus = ref('')
const groupByAssignee = ref(false)

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'claimed', label: '已认领' },
  { value: 'in_progress', label: '进行中' },
  { value: 'submitted', label: '已提交' },
  { value: 'confirmed', label: '已确认' },
  { value: 'archived', label: '已归档' },
]

const filteredTasks = computed(() => {
  let list = [...props.tasks]
  if (keyword.value) {
    list = list.filter(t => t.task_title.includes(keyword.value))
  }
  if (filterPriority.value) {
    list = list.filter(t => t.priority === filterPriority.value)
  }
  if (filterStatus.value) {
    list = list.filter(t => t.status === filterStatus.value)
  }
  return list
})

const PRIORITY_COLORS: Record<string, string> = {
  P0: '#F56C6C',
  P1: '#E6A23C',
  P2: '#909399',
}

function getBarColor(task: ProjectScheduleTask): string {
  const todayStr = new Date().toISOString().slice(0, 10)
  if (['confirmed', 'archived'].includes(task.status)) return '#67C23A'
  if (task.status === 'submitted') return '#E6A23C'
  if (task.scheduled_end && task.scheduled_end < todayStr &&
      ['claimed', 'in_progress'].includes(task.status)) return '#F56C6C'
  if (['claimed', 'in_progress'].includes(task.status)) return '#409EFF'
  return '#DCDFE6'
}

function buildChartOption(tasks: ProjectScheduleTask[]) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayTs = today.getTime()

  let sortedTasks: ProjectScheduleTask[]
  if (groupByAssignee.value) {
    const grouped = new Map<string, ProjectScheduleTask[]>()
    for (const t of tasks) {
      const key = t.assignee_name || '未分配'
      if (!grouped.has(key)) grouped.set(key, [])
      grouped.get(key)!.push(t)
    }
    sortedTasks = []
    for (const [, members] of grouped) {
      sortedTasks.push(...members)
    }
  } else {
    const priorityOrder: Record<string, number> = { P0: 0, P1: 1, P2: 2 }
    sortedTasks = [...tasks].sort(
      (a, b) => (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2)
    )
  }

  const yCategories = sortedTasks.map((t, i) => {
    const prefix = t.priority === 'P0' ? '🔴' : t.priority === 'P1' ? '🟠' : '⚪'
    const assignee = t.assignee_name ? ` (${t.assignee_name})` : ''
    return `${prefix} ${t.task_title}${assignee}`
  })

  // 计算时间范围
  const allDates: number[] = [todayTs]
  for (const t of sortedTasks) {
    if (t.scheduled_start) allDates.push(new Date(t.scheduled_start).getTime())
    if (t.scheduled_end) allDates.push(new Date(t.scheduled_end).getTime())
    if (t.deadline) allDates.push(new Date(t.deadline).getTime())
  }
  const minDate = Math.min(...allDates) - 7 * 86400000
  const maxDate = Math.max(...allDates) + 14 * 86400000

  // 构建 custom series data
  const seriesData: any[] = []
  sortedTasks.forEach((task, idx) => {
    if (!task.scheduled_start || !task.scheduled_end) {
      // 未排期任务：不画条，只在图上做标记
      return
    }
    const startTs = new Date(task.scheduled_start).getTime()
    const endTs = new Date(task.scheduled_end).getTime() + 86400000 // end 是最后一天，+1天

    seriesData.push({
      value: [idx, startTs, endTs, task.task_id],
      itemStyle: { color: getBarColor(task) },
      task,
    })
  })

  const option: echarts.EChartsOption = {
    tooltip: {
      formatter: (params: any) => {
        const task: ProjectScheduleTask = params.data?.task
        if (!task) return ''
        const start = task.scheduled_start || '-'
        const end = task.scheduled_end || '-'
        const deadline = task.deadline ? `<br/>截止：${task.deadline}` : ''
        return [
          `<b>${task.task_title}</b>`,
          `优先级：${task.priority}  |  状态：${task.status}`,
          `负责人：${task.assignee_name || '未分配'}`,
          `排期：${start} ～ ${end}`,
          `拟投入：${task.estimated_man_days} 天`,
          deadline,
        ].join('<br/>')
      },
    },
    grid: {
      top: 20,
      bottom: 40,
      left: 220,
      right: 60,
    },
    xAxis: {
      type: 'time',
      min: minDate,
      max: maxDate,
      axisLabel: {
        formatter: (val: number) => {
          const d = new Date(val)
          return `${d.getMonth() + 1}/${d.getDate()}`
        },
        fontSize: 11,
      },
      splitLine: { show: true, lineStyle: { color: '#f0f0f0' } },
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: {
        fontSize: 11,
        width: 200,
        overflow: 'truncate',
      },
      inverse: true,
    },
    series: [
      {
        type: 'custom',
        renderItem: (params: any, api: any) => {
          const yIndex = api.value(0)
          const startTime = api.value(1)
          const endTime = api.value(2)
          const coordStart = api.coord([startTime, yIndex])
          const coordEnd = api.coord([endTime, yIndex])
          const barHeight = api.size([0, 1])[1] * 0.6
          return {
            type: 'rect',
            shape: {
              x: coordStart[0],
              y: coordStart[1] - barHeight / 2,
              width: Math.max(coordEnd[0] - coordStart[0], 4),
              height: barHeight,
            },
            style: {
              ...api.style(),
              borderRadius: 3,
            },
          }
        },
        data: seriesData,
        encode: { x: [1, 2], y: 0 },
      },
    ],
    // 今日竖线
    graphic: [
      {
        type: 'line',
        z: 100,
        shape: { x1: 0, y1: 0, x2: 0, y2: 0 },
        style: { stroke: '#409EFF', lineWidth: 2, lineDash: [4, 3] },
        silent: true,
      },
    ],
  }

  return { option, todayTs }
}

function renderChart() {
  if (!chartRef.value || !chart) return
  if (filteredTasks.value.length === 0) return

  const { option, todayTs } = buildChartOption(filteredTasks.value)
  chart.setOption(option, true)

  // 更新今日竖线位置
  nextTick(() => {
    if (!chart) return
    const coordSys = (chart as any).getModel()?.getComponent('xAxis')
    try {
      const todayPixel = chart.convertToPixel({ xAxisIndex: 0 }, todayTs)
      const grid = (chart as any).getModel()?.getComponent('grid')
      const gridRect = grid?.coordinateSystem?.getRect?.()
      if (todayPixel != null && gridRect) {
        chart.setOption({
          graphic: [
            {
              type: 'line',
              z: 100,
              shape: {
                x1: todayPixel,
                y1: gridRect.y,
                x2: todayPixel,
                y2: gridRect.y + gridRect.height,
              },
              style: { stroke: '#409EFF', lineWidth: 2, lineDash: [4, 3] },
              silent: true,
            },
          ],
        })
      }
    } catch {}
  })
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    if (filteredTasks.value.length > 0) renderChart()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})

const handleResize = () => chart?.resize()

watch(
  [filteredTasks, groupByAssignee],
  async () => {
    await nextTick()
    if (chart && filteredTasks.value.length > 0) {
      // 动态调整高度
      const height = Math.max(300, filteredTasks.value.length * 40 + 80)
      chartRef.value!.style.height = `${height}px`
      chart.resize()
      renderChart()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.project-gantt-chart {
  padding: 0;
}

.gantt-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.gantt-container {
  width: 100%;
  min-height: 300px;
  height: 400px;
}

.gantt-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.legend-bar {
  display: inline-block;
  width: 24px;
  height: 10px;
  border-radius: 2px;
}

.legend-dashed {
  background: transparent;
  border: 2px dashed #c0c4cc;
}
</style>
