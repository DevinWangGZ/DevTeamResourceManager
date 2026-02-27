<template>
  <div class="personal-schedule-calendar">
    <!-- 工具栏 -->
    <div class="calendar-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button @click="prevPeriod">
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <el-button @click="goToday">今天</el-button>
          <el-button @click="nextPeriod">
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-button-group>
        <span class="period-label">{{ periodLabel }}</span>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="month">月视图</el-radio-button>
          <el-radio-button label="week">周视图</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend">
      <span class="legend-item">
        <span class="legend-dot" style="background: #F56C6C"></span> P0 最紧急
      </span>
      <span class="legend-item">
        <span class="legend-dot" style="background: #E6A23C"></span> P1 较紧急
      </span>
      <span class="legend-item">
        <span class="legend-dot" style="background: #909399"></span> P2 常规
      </span>
      <span class="legend-item">
        <span class="legend-dot" style="background: transparent; border: 2px solid #F56C6C"></span> 延误
      </span>
      <span class="legend-item">
        <span class="legend-dot" style="background: #67C23A"></span> 配合任务
      </span>
    </div>

    <!-- 月视图 -->
    <div v-if="viewMode === 'month'" class="month-grid" v-loading="loading">
      <div class="weekday-header">
        <div v-for="d in weekdays" :key="d" class="weekday-cell">{{ d }}</div>
      </div>
      <div class="month-body">
        <div
          v-for="week in monthWeeks"
          :key="week[0].dateStr"
          class="week-row"
        >
          <div
            v-for="day in week"
            :key="day.dateStr"
            class="day-cell"
            :class="{
              'other-month': !day.isCurrentMonth,
              'is-today': day.isToday,
              'is-weekend': day.isWeekend,
            }"
          >
            <div class="day-number">{{ day.day }}</div>
            <div class="task-slots">
              <div
                v-for="(item, idx) in day.tasks.slice(0, 3)"
                :key="item.task_id + '-' + idx"
                class="task-chip"
                :class="{
                  'overdue': item.isOverdue,
                  'concurrent': item.is_concurrent,
                  'collaborator': item.role === 'collaborator',
                }"
                :style="{ background: getTaskChipColor(item), cursor: 'pointer' }"
                @click="openTaskPopover(item)"
              >
                <span v-if="item.is_concurrent" class="concurrent-badge">⇄</span>
                {{ item.task_title }}
              </div>
              <div
                v-if="day.tasks.length > 3"
                class="task-chip-more"
                @click="openDayTasksDialog(day)"
              >
                +{{ day.tasks.length - 3 }} 更多
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 周视图 -->
    <div v-else class="week-view" v-loading="loading">
      <div class="week-header">
        <div class="time-col-header"></div>
        <div
          v-for="day in currentWeekDays"
          :key="day.dateStr"
          class="week-day-header"
          :class="{ 'is-today': day.isToday }"
        >
          <div class="week-day-name">{{ day.weekdayName }}</div>
          <div class="week-day-date">{{ day.day }}</div>
        </div>
      </div>
      <div class="week-body">
        <div class="time-col">
          <div v-for="day in currentWeekDays" :key="day.dateStr" class="week-day-tasks">
            <div
              v-for="(item, idx) in day.tasks"
              :key="item.task_id + '-' + idx"
              class="task-block"
              :class="{ 'overdue': item.isOverdue, 'collaborator': item.role === 'collaborator' }"
              :style="{ background: getTaskChipColor(item) }"
              @click="openTaskPopover(item)"
            >
              <div class="task-block-priority">{{ item.priority }}</div>
              <div class="task-block-title">{{ item.task_title }}</div>
              <div class="task-block-days">{{ item.estimated_days }}天</div>
            </div>
            <div v-if="day.tasks.length === 0" class="no-task">-</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务详情 Popover -->
    <el-dialog
      v-model="showTaskPopover"
      :title="selectedTask?.task_title"
      width="420px"
      append-to-body
    >
      <template v-if="selectedTask">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="优先级">
            <PriorityTag :priority="selectedTask.priority" />
          </el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag :type="selectedTask.role === 'assignee' ? 'primary' : 'success'" size="small">
              {{ selectedTask.role === 'assignee' ? '主认领人' : '配合人' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="排期">
            {{ selectedTask.scheduled_start }} ～ {{ selectedTask.scheduled_end }}
          </el-descriptions-item>
          <el-descriptions-item label="拟投入">{{ selectedTask.estimated_days }} 天</el-descriptions-item>
          <el-descriptions-item label="状态">{{ getStatusText(selectedTask.status) }}</el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.is_concurrent" label="并发模式">
            <el-tag type="success" size="small">并发任务</el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.is_pinned" label="置顶">
            <el-tag type="warning" size="small">已置顶</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="showTaskPopover = false">关闭</el-button>
        <el-button type="primary" @click="goToTask">查看详情</el-button>
      </template>
    </el-dialog>

    <!-- 当日任务列表弹窗 -->
    <el-dialog
      v-model="showDayTasksDialog"
      :title="dayTasksDate + ' 全部任务'"
      width="480px"
      append-to-body
    >
      <div v-for="item in dayTasksList" :key="item.task_id" class="day-task-item">
        <PriorityTag :priority="item.priority" :show-label="false" />
        <span class="day-task-title">{{ item.task_title }}</span>
        <el-tag size="small" :type="item.role === 'assignee' ? 'primary' : 'success'">
          {{ item.role === 'assignee' ? '主认领' : '配合' }}
        </el-tag>
        <el-button link size="small" type="primary" @click="openTaskPopover(item)">
          详情
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import PriorityTag from './PriorityTag.vue'
import { getMySchedule, type UserScheduleItem } from '@/api/task'

const router = useRouter()

const viewMode = ref<'month' | 'week'>('month')
const loading = ref(false)
const currentDate = ref(new Date())
const scheduleItems = ref<UserScheduleItem[]>([])

const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const today = new Date()
today.setHours(0, 0, 0, 0)

const toDateStr = (d: Date) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const periodLabel = computed(() => {
  const d = currentDate.value
  if (viewMode.value === 'month') {
    return `${d.getFullYear()}年${d.getMonth() + 1}月`
  } else {
    const weekStart = getWeekStart(d)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    return `${toDateStr(weekStart)} ～ ${toDateStr(weekEnd)}`
  }
})

const getWeekStart = (d: Date) => {
  const day = d.getDay()
  const result = new Date(d)
  result.setDate(d.getDate() - day)
  result.setHours(0, 0, 0, 0)
  return result
}

function prevPeriod() {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() - 1)
  } else {
    d.setDate(d.getDate() - 7)
  }
  currentDate.value = d
}

function nextPeriod() {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() + 1)
  } else {
    d.setDate(d.getDate() + 7)
  }
  currentDate.value = d
}

function goToday() {
  currentDate.value = new Date()
}

// 将 schedule item 映射到日期范围内的每一天
const buildDayTaskMap = () => {
  const map: Record<string, (UserScheduleItem & { isOverdue: boolean })[]> = {}
  const todayStr = toDateStr(today)

  for (const item of scheduleItems.value) {
    if (!item.scheduled_start || !item.scheduled_end) continue
    const start = new Date(item.scheduled_start)
    const end = new Date(item.scheduled_end)
    const isOverdue =
      item.scheduled_end < todayStr &&
      ['claimed', 'in_progress'].includes(item.status)

    let cur = new Date(start)
    while (cur <= end) {
      const key = toDateStr(cur)
      if (!map[key]) map[key] = []
      map[key].push({ ...item, isOverdue })
      cur.setDate(cur.getDate() + 1)
    }
  }
  return map
}

const monthWeeks = computed(() => {
  const d = currentDate.value
  const year = d.getFullYear()
  const month = d.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  const dayMap = buildDayTaskMap()
  const weeks: any[][] = []
  let week: any[] = []

  // 填充第一周前面的空白（上月末尾）
  for (let i = 0; i < firstDay.getDay(); i++) {
    const prevDate = new Date(firstDay)
    prevDate.setDate(prevDate.getDate() - (firstDay.getDay() - i))
    const dateStr = toDateStr(prevDate)
    week.push({
      date: prevDate,
      dateStr,
      day: prevDate.getDate(),
      isCurrentMonth: false,
      isToday: dateStr === toDateStr(today),
      isWeekend: prevDate.getDay() === 0 || prevDate.getDay() === 6,
      tasks: dayMap[dateStr] || [],
    })
  }

  for (let dd = 1; dd <= lastDay.getDate(); dd++) {
    const cur = new Date(year, month, dd)
    const dateStr = toDateStr(cur)
    week.push({
      date: cur,
      dateStr,
      day: dd,
      isCurrentMonth: true,
      isToday: dateStr === toDateStr(today),
      isWeekend: cur.getDay() === 0 || cur.getDay() === 6,
      tasks: dayMap[dateStr] || [],
    })
    if (week.length === 7) {
      weeks.push(week)
      week = []
    }
  }

  // 填充最后一周后面的空白
  if (week.length > 0) {
    let nextDay = new Date(lastDay)
    nextDay.setDate(nextDay.getDate() + 1)
    while (week.length < 7) {
      const dateStr = toDateStr(nextDay)
      week.push({
        date: new Date(nextDay),
        dateStr,
        day: nextDay.getDate(),
        isCurrentMonth: false,
        isToday: dateStr === toDateStr(today),
        isWeekend: nextDay.getDay() === 0 || nextDay.getDay() === 6,
        tasks: dayMap[dateStr] || [],
      })
      nextDay.setDate(nextDay.getDate() + 1)
    }
    weeks.push(week)
  }

  return weeks
})

const currentWeekDays = computed(() => {
  const weekStart = getWeekStart(currentDate.value)
  const dayMap = buildDayTaskMap()
  return Array.from({ length: 7 }, (_, i) => {
    const cur = new Date(weekStart)
    cur.setDate(cur.getDate() + i)
    const dateStr = toDateStr(cur)
    return {
      date: cur,
      dateStr,
      day: cur.getDate(),
      weekdayName: weekdayNames[cur.getDay()],
      isToday: dateStr === toDateStr(today),
      tasks: dayMap[dateStr] || [],
    }
  })
})

const PRIORITY_COLORS: Record<string, string> = {
  P0: '#F56C6C',
  P1: '#E6A23C',
  P2: '#909399',
}

function getTaskChipColor(item: UserScheduleItem & { isOverdue?: boolean }) {
  if (item.isOverdue) return '#F56C6C'
  if (item.role === 'collaborator') return '#67C23A'
  return PRIORITY_COLORS[item.priority] || '#909399'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    pending_eval: '待评估',
    claimed: '已认领',
    in_progress: '进行中',
    submitted: '已提交',
    confirmed: '已确认',
    archived: '已归档',
  }
  return map[status] || status
}

// 任务详情弹窗
const showTaskPopover = ref(false)
const selectedTask = ref<(UserScheduleItem & { isOverdue?: boolean }) | null>(null)

function openTaskPopover(item: any) {
  selectedTask.value = item
  showTaskPopover.value = true
}

function goToTask() {
  if (!selectedTask.value) return
  router.push(`/tasks/${selectedTask.value.task_id}`)
  showTaskPopover.value = false
}

// 当日任务列表弹窗
const showDayTasksDialog = ref(false)
const dayTasksDate = ref('')
const dayTasksList = ref<any[]>([])

function openDayTasksDialog(day: any) {
  dayTasksDate.value = day.dateStr
  dayTasksList.value = day.tasks
  showDayTasksDialog.value = true
}

// 加载排期数据
const loadSchedule = async () => {
  loading.value = true
  try {
    const d = currentDate.value
    let startDate: string
    let endDate: string
    if (viewMode.value === 'month') {
      const year = d.getFullYear()
      const month = d.getMonth()
      startDate = toDateStr(new Date(year, month, 1))
      endDate = toDateStr(new Date(year, month + 1, 0))
    } else {
      const weekStart = getWeekStart(d)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)
      startDate = toDateStr(weekStart)
      endDate = toDateStr(weekEnd)
    }
    const res = await getMySchedule({ start_date: startDate, end_date: endDate })
    scheduleItems.value = res.schedule
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '加载排期失败')
  } finally {
    loading.value = false
  }
}

watch([currentDate, viewMode], loadSchedule, { immediate: false })
onMounted(loadSchedule)
</script>

<style scoped>
.personal-schedule-calendar {
  padding: 0;
}

.calendar-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.period-label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.legend {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

/* 月视图 */
.month-grid {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #f5f7fa;
}

.weekday-cell {
  text-align: center;
  padding: 8px 0;
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  border-right: 1px solid #e4e7ed;
}

.weekday-cell:last-child {
  border-right: none;
}

.month-body {
  display: flex;
  flex-direction: column;
}

.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-top: 1px solid #e4e7ed;
  min-height: 80px;
}

.day-cell {
  border-right: 1px solid #e4e7ed;
  padding: 4px;
  min-height: 80px;
  vertical-align: top;
}

.day-cell:last-child {
  border-right: none;
}

.day-cell.other-month .day-number {
  color: #c0c4cc;
}

.day-cell.is-today {
  background: #ecf5ff;
}

.day-cell.is-today .day-number {
  background: #409eff;
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.day-cell.is-weekend {
  background: #fafafa;
}

.day-number {
  font-size: 12px;
  color: #303133;
  margin-bottom: 2px;
}

.task-slots {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-chip {
  font-size: 11px;
  color: #fff;
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.task-chip.overdue {
  outline: 2px solid #F56C6C;
  outline-offset: -2px;
}

.task-chip.concurrent::before {
  content: '⇄ ';
}

.task-chip-more {
  font-size: 11px;
  color: #409eff;
  cursor: pointer;
  padding-left: 4px;
}

.concurrent-badge {
  font-size: 10px;
  margin-right: 2px;
}

/* 周视图 */
.week-view {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.week-header {
  display: grid;
  grid-template-columns: 0 repeat(7, 1fr);
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.time-col-header {
  border-right: 1px solid #e4e7ed;
}

.week-day-header {
  text-align: center;
  padding: 8px 4px;
  border-right: 1px solid #e4e7ed;
}

.week-day-header:last-child {
  border-right: none;
}

.week-day-header.is-today {
  background: #ecf5ff;
}

.week-day-name {
  font-size: 12px;
  color: #606266;
}

.week-day-date {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.week-body {
  display: grid;
  grid-template-columns: 0 repeat(7, 1fr);
}

.time-col {
  display: contents;
}

.week-day-tasks {
  padding: 8px 4px;
  border-right: 1px solid #e4e7ed;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.week-day-tasks:last-child {
  border-right: none;
}

.task-block {
  border-radius: 4px;
  padding: 4px 6px;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
}

.task-block.overdue {
  outline: 2px solid #F56C6C;
}

.task-block-priority {
  font-size: 10px;
  font-weight: bold;
  margin-bottom: 2px;
}

.task-block-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-block-days {
  font-size: 10px;
  opacity: 0.8;
  margin-top: 2px;
}

.no-task {
  color: #c0c4cc;
  font-size: 12px;
  text-align: center;
  padding: 8px 0;
}

/* 当日任务弹窗 */
.day-task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.day-task-item:last-child {
  border-bottom: none;
}

.day-task-title {
  flex: 1;
  font-size: 13px;
}
</style>
