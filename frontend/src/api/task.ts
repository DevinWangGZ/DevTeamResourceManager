/**
 * 任务管理API
 */
import request from './index'

// 优先级常量
export const PRIORITY_OPTIONS = [
  { value: 'P2', label: 'P2 常规', color: '#909399', multiplier: 1.0 },
  { value: 'P1', label: 'P1 较紧急', color: '#E6A23C', multiplier: 1.1 },
  { value: 'P0', label: 'P0 最紧急', color: '#F56C6C', multiplier: 1.2 },
] as const

export type TaskPriority = 'P0' | 'P1' | 'P2'

export const PRIORITY_MULTIPLIER: Record<TaskPriority, number> = {
  P0: 1.2,
  P1: 1.1,
  P2: 1.0,
}

export interface TaskScheduleInfo {
  start_date?: string
  end_date?: string
  is_pinned: boolean
  is_concurrent: boolean
  concurrent_with?: number
}

export interface Task {
  id: number
  title: string
  description?: string
  status: string
  project_id?: number
  creator_id: number
  assignee_id?: number
  estimated_man_days: number
  actual_man_days?: number
  required_skills?: string
  deadline?: string
  is_pinned: boolean
  rejection_reason?: string
  priority: TaskPriority
  priority_multiplier: number
  schedule?: TaskScheduleInfo
  created_at: string
  updated_at: string
}

export interface TaskDetail extends Task {
  creator_name?: string
  assignee_name?: string
  project_name?: string
}

export interface TaskCreate {
  title: string
  description?: string
  project_id?: number
  estimated_man_days: number
  required_skills?: string
  deadline?: string
  priority?: TaskPriority
}

export interface TaskUpdate {
  title?: string
  description?: string
  project_id?: number
  estimated_man_days?: number
  required_skills?: string
  deadline?: string
  priority?: TaskPriority
}

export interface TaskListResponse {
  total: number
  items: Task[]
}

export interface TaskFilterParams {
  status?: string
  project_id?: number
  creator_id?: number
  assignee_id?: number
  keyword?: string
  priority?: TaskPriority
  page?: number
  page_size?: number
}

export interface TaskAssign {
  assignee_id: number
}

export interface TaskEvaluate {
  accept: boolean
}

export interface TaskSubmit {
  actual_man_days: number
}

export interface TaskPin {
  is_pinned: boolean
}

// ---- 并发排期相关类型 ----

export interface SetConcurrentRequest {
  concurrent_with_task_id: number
}

export interface ExceededUser {
  user_id: number
  name: string
  current_concurrent: number
  limit: number
}

export interface AffectedSchedule {
  task_id: number
  task_title: string
  old_scheduled_start?: string
  new_scheduled_start?: string
}

export interface ConcurrentCheckResponse {
  can_set_concurrent: boolean
  exceeded_users: ExceededUser[]
  affected_schedules: AffectedSchedule[]
}

// ---- 个人日程类型 ----

export interface UserScheduleItem {
  task_id: number
  task_title: string
  priority: TaskPriority
  scheduled_start?: string
  scheduled_end?: string
  status: string
  estimated_days: number
  is_concurrent: boolean
  concurrent_with?: number
  role: 'assignee' | 'collaborator'
  is_pinned: boolean
}

export interface UserScheduleResponse {
  schedule: UserScheduleItem[]
}

// ---- 项目排期类型 ----

export interface ProjectScheduleTask {
  task_id: number
  task_title: string
  priority: TaskPriority
  priority_multiplier: number
  assignee_id?: number
  assignee_name?: string
  scheduled_start?: string
  scheduled_end?: string
  status: string
  estimated_man_days: number
  actual_man_days?: number
  is_concurrent: boolean
  concurrent_with?: number
  deadline?: string
}

export interface ProjectScheduleResponse {
  project_id: number
  project_name: string
  tasks: ProjectScheduleTask[]
}

/**
 * 创建任务
 */
export function createTask(data: TaskCreate): Promise<Task> {
  return request.post('/api/v1/tasks', data)
}

/**
 * 获取任务列表
 */
export function getTasks(params?: TaskFilterParams): Promise<TaskListResponse> {
  return request.get('/api/v1/tasks', { params })
}

/**
 * 获取任务详情
 */
export function getTask(taskId: number): Promise<TaskDetail> {
  return request.get(`/api/v1/tasks/${taskId}`)
}

/**
 * 更新任务
 */
export function updateTask(taskId: number, data: TaskUpdate): Promise<Task> {
  return request.put(`/api/v1/tasks/${taskId}`, data)
}

/**
 * 删除任务
 */
export function deleteTask(taskId: number): Promise<void> {
  return request.delete(`/api/v1/tasks/${taskId}`)
}

export interface MarketplaceTask {
  id: number
  title: string
  description?: string
  status: string
  project_id?: number
  project_name?: string
  creator_id: number
  creator_name?: string
  estimated_man_days: number
  required_skills?: string
  deadline?: string
  created_at?: string
  priority: TaskPriority
  priority_multiplier: number
}

export interface MarketplaceResponse {
  tasks: MarketplaceTask[]
  total: number
  page: number
  page_size: number
}

/**
 * 获取任务集市数据
 */
export function getMarketplaceTasks(params?: {
  status?: string
  project_id?: number
  keyword?: string
  required_skills?: string
  priority?: TaskPriority
  recommend?: boolean
  page?: number
  page_size?: number
}): Promise<MarketplaceResponse> {
  return request.get('/api/v1/tasks/marketplace', { params })
}

/**
 * 发布任务
 */
export function publishTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/publish`)
}

/**
 * 认领人退回 / 发起人收回已认领任务，回到"已发布"状态
 */
export function returnTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/return`)
}

/**
 * 将已发布任务退回草稿
 */
export function revertTaskToDraft(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/revert-draft`)
}

// ---- 任务配合人 ----

export interface Collaborator {
  id: number
  task_id: number
  user_id: number
  user_name?: string
  user_full_name?: string
  allocated_man_days: number
  scheduled_start?: string
  scheduled_end?: string
  created_at: string
}

/**
 * 获取任务配合人列表
 */
export function getCollaborators(taskId: number): Promise<Collaborator[]> {
  return request.get(`/api/v1/tasks/${taskId}/collaborators`)
}

/**
 * 添加配合人
 */
export function addCollaborator(
  taskId: number,
  data: { user_id: number; allocated_man_days: number }
): Promise<Collaborator> {
  return request.post(`/api/v1/tasks/${taskId}/collaborators`, data)
}

/**
 * 更新配合人分配人天
 */
export function updateCollaborator(
  taskId: number,
  collaboratorUserId: number,
  data: { allocated_man_days: number }
): Promise<Collaborator> {
  return request.put(`/api/v1/tasks/${taskId}/collaborators/${collaboratorUserId}`, data)
}

/**
 * 移除配合人
 */
export function removeCollaborator(taskId: number, collaboratorUserId: number): Promise<void> {
  return request.delete(`/api/v1/tasks/${taskId}/collaborators/${collaboratorUserId}`)
}

/**
 * 认领任务
 */
export function claimTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/claim`)
}

/**
 * 派发任务
 */
export function assignTask(taskId: number, data: TaskAssign): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/assign`, data)
}

/**
 * 评估任务（接受或拒绝）
 */
export function evaluateTask(taskId: number, data: TaskEvaluate): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/evaluate`, data)
}

/**
 * 开始任务
 */
export function startTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/start`)
}

/**
 * 提交任务
 */
export function submitTask(taskId: number, data: TaskSubmit): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/submit`, data)
}

/**
 * 确认任务
 */
export function confirmTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/confirm`)
}

/**
 * 退回已提交任务（发起人/PM），附带退回原因，任务回到"进行中"状态
 */
export function rejectTask(taskId: number, reason: string): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/reject`, { reason })
}

/**
 * 置顶/取消置顶任务
 */
export function pinTask(taskId: number, data: TaskPin): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/pin`, data)
}

/**
 * 获取任务排期
 */
export function getTaskSchedule(taskId: number): Promise<any> {
  return request.get(`/api/v1/tasks/${taskId}/schedule`)
}

// ---- 并发排期接口 ----

/**
 * 并发预检（不执行实际设置）
 */
export function checkConcurrent(
  taskId: number,
  concurrentWithTaskId: number
): Promise<ConcurrentCheckResponse> {
  return request.get(`/api/v1/tasks/${taskId}/concurrent-check`, {
    params: { concurrent_with_task_id: concurrentWithTaskId },
  })
}

/**
 * 设置任务为并发
 */
export function setConcurrent(
  taskId: number,
  data: SetConcurrentRequest
): Promise<any> {
  return request.post(`/api/v1/tasks/${taskId}/set-concurrent`, data)
}

/**
 * 取消任务并发状态
 */
export function unsetConcurrent(taskId: number): Promise<any> {
  return request.delete(`/api/v1/tasks/${taskId}/set-concurrent`)
}

/**
 * 获取当前用户的完整排期
 */
export function getMySchedule(params?: {
  start_date?: string
  end_date?: string
}): Promise<UserScheduleResponse> {
  return request.get('/api/v1/tasks/me/schedule', { params })
}

/**
 * 手动触发当前用户排期重算（任务提前完成后使用）
 */
export function recalculateMySchedule(): Promise<{ success: boolean; message: string }> {
  return request.post('/api/v1/tasks/me/recalculate-schedule')
}

/**
 * 获取项目排期（甘特图数据）
 */
export function getProjectSchedule(projectId: number): Promise<ProjectScheduleResponse> {
  return request.get(`/api/v1/projects/${projectId}/schedule`)
}

// ── 任务留言 ─────────────────────────────────────────────────────────────────

export interface TaskComment {
  id: number
  task_id: number
  user_id: number
  user_name: string
  user_full_name?: string
  content: string
  created_at: string
  updated_at: string
}

export interface TaskCommentListResponse {
  total: number
  items: TaskComment[]
}

/**
 * 获取任务留言列表
 */
export function getTaskComments(taskId: number): Promise<TaskCommentListResponse> {
  return request.get(`/api/v1/tasks/${taskId}/comments`)
}

/**
 * 发表任务留言
 */
export function createTaskComment(taskId: number, content: string): Promise<TaskComment> {
  return request.post(`/api/v1/tasks/${taskId}/comments`, { content })
}

/**
 * 编辑留言
 */
export function updateTaskComment(commentId: number, content: string): Promise<TaskComment> {
  return request.put(`/api/v1/tasks/comments/${commentId}`, { content })
}

/**
 * 删除留言
 */
export function deleteTaskComment(commentId: number): Promise<void> {
  return request.delete(`/api/v1/tasks/comments/${commentId}`)
}
