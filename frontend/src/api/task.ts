/**
 * 任务管理API
 */
import request from './index'
import type { AxiosResponse } from 'axios'

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
}

export interface TaskUpdate {
  title?: string
  description?: string
  project_id?: number
  estimated_man_days?: number
  required_skills?: string
  deadline?: string
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

/**
 * 发布任务
 */
export function publishTask(taskId: number): Promise<Task> {
  return request.post(`/api/v1/tasks/${taskId}/publish`)
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
