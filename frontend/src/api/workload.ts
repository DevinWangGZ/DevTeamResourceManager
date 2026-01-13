/**
 * 工作量统计API
 */
import request from './index'

export interface WorkloadStatistic {
  id: number
  user_id: number
  project_id?: number
  project_name?: string
  total_man_days: number
  period_start: string
  period_end: string
  created_at: string
  updated_at: string
}

export interface WorkloadStatisticListResponse {
  total: number
  items: WorkloadStatistic[]
}

export interface WorkloadSummary {
  user_id: number
  user_name: string
  total_man_days: number
  project_count: number
  period_start: string
  period_end: string
}

export interface WorkloadFilterParams {
  user_id?: number
  project_id?: number
  period_start?: string
  period_end?: string
  skip?: number
  limit?: number
}

/**
 * 获取工作量统计列表
 */
export function getWorkloadStatistics(params?: WorkloadFilterParams): Promise<WorkloadStatisticListResponse> {
  return request.get('/api/v1/workload-statistics', { params })
}

/**
 * 获取当前用户的工作量统计
 */
export function getMyWorkloadStatistics(params?: {
  project_id?: number
  period_start?: string
  period_end?: string
}): Promise<WorkloadStatisticListResponse> {
  return request.get('/api/v1/workload-statistics/my', { params })
}

/**
 * 获取当前用户的工作量汇总
 */
export function getMyWorkloadSummary(params?: {
  period_start?: string
  period_end?: string
}): Promise<WorkloadSummary> {
  return request.get('/api/v1/workload-statistics/summary', { params })
}

/**
 * 获取指定项目的工作量统计
 */
export function getProjectWorkloadStatistics(
  projectId: number,
  params?: {
    period_start?: string
    period_end?: string
  }
): Promise<WorkloadStatisticListResponse> {
  return request.get(`/api/v1/workload-statistics/project/${projectId}`, { params })
}
