/**
 * 项目API
 */
import request from './index'

export interface Project {
  id: number
  name: string
  description?: string
  estimated_output_value?: number
  created_by: number
  creator_name?: string
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  estimated_output_value?: number
}

export interface ProjectUpdate {
  name?: string
  description?: string
  estimated_output_value?: number
}

export interface ProjectListResponse {
  total: number
  items: Project[]
}

/**
 * 获取项目列表
 */
export function getProjects(params?: {
  creator_id?: number
  skip?: number
  limit?: number
}): Promise<ProjectListResponse> {
  return request.get('/api/v1/projects', { params })
}

/**
 * 获取项目详情
 */
export function getProject(projectId: number): Promise<Project> {
  return request.get(`/api/v1/projects/${projectId}`)
}

/**
 * 创建项目
 */
export function createProject(data: ProjectCreate): Promise<Project> {
  return request.post('/api/v1/projects', data)
}

/**
 * 更新项目
 */
export function updateProject(projectId: number, data: ProjectUpdate): Promise<Project> {
  return request.put(`/api/v1/projects/${projectId}`, data)
}

/**
 * 删除项目
 */
export function deleteProject(projectId: number): Promise<void> {
  return request.delete(`/api/v1/projects/${projectId}`)
}

export interface ProjectTask {
  id: number
  title: string
  description?: string
  status: string
  creator_id: number
  creator_name?: string
  assignee_id?: number
  assignee_name?: string
  estimated_man_days: number
  actual_man_days?: number
  required_skills?: string
  deadline?: string
  is_pinned: boolean
  created_at?: string
  updated_at?: string
  schedule?: {
    start_date?: string
    end_date?: string
    work_days: number
    is_pinned: boolean
  }
}

export interface ProjectTaskExecutionResponse {
  project_id: number
  project_name: string
  tasks: ProjectTask[]
  status_summary: Record<string, number>
  total: number
}

/**
 * 获取项目任务执行视图数据
 */
export function getProjectTasks(
  projectId: number,
  params?: {
    status?: string
    assignee_id?: number
    keyword?: string
  }
): Promise<ProjectTaskExecutionResponse> {
  return request.get(`/api/v1/projects/${projectId}/tasks`, { params })
}
