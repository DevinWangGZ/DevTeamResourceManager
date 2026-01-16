/**
 * 数据导出API
 */
import request from './index'

/**
 * 导出工作量统计数据
 */
export function exportWorkloadStatistics(params?: {
  user_id?: number
  project_id?: number
  period_start?: string
  period_end?: string
}): Promise<Blob> {
  return request.get('/api/v1/export/workload-statistics', {
    params,
    responseType: 'blob',
  })
}

/**
 * 导出任务数据
 */
export function exportTasks(params?: {
  status?: string
  project_id?: number
  creator_id?: number
  assignee_id?: number
}): Promise<Blob> {
  return request.get('/api/v1/export/tasks', {
    params,
    responseType: 'blob',
  })
}

/**
 * 导出绩效数据
 */
export function exportPerformanceData(params?: {
  user_id?: number
  period_start?: string
  period_end?: string
}): Promise<Blob> {
  return request.get('/api/v1/export/performance', {
    params,
    responseType: 'blob',
  })
}
