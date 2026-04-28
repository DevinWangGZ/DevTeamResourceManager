/**
 * 数据导出API
 */
import request from './index'

const EXPORT_TIMEOUT_MS = 600000

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
    timeout: EXPORT_TIMEOUT_MS,
  })
}

/**
 * 导出任务数据
 */
export function exportTasks(params?: {
  status?: string
  statuses?: string
  project_id?: number
  project_ids?: string
  creator_id?: number
  creator_ids?: string
  assignee_id?: number
  assignee_ids?: string
  keyword?: string
  required_skills?: string
  priority?: string
  embed_images?: boolean
}): Promise<Blob> {
  return request.get('/api/v1/export/tasks', {
    params,
    responseType: 'blob',
    timeout: EXPORT_TIMEOUT_MS,
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
    timeout: EXPORT_TIMEOUT_MS,
  })
}
