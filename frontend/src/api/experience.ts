/**
 * 业务履历管理API
 */
import request from './index'

export interface Experience {
  id: number
  user_id: number
  project: string
  module?: string
  role?: string
  description?: string
  man_days: number
  created_at: string
  updated_at: string
}

export interface ExperienceCreate {
  project: string
  module?: string
  role?: string
  description?: string
  man_days: number
}

export interface ExperienceUpdate {
  project?: string
  module?: string
  role?: string
  description?: string
  man_days?: number
}

export interface ExperienceListResponse {
  total: number
  items: Experience[]
}

/**
 * 创建业务履历
 */
export function createExperience(data: ExperienceCreate): Promise<Experience> {
  return request.post('/api/v1/experiences', data)
}

/**
 * 获取业务履历列表
 */
export function getExperiences(): Promise<ExperienceListResponse> {
  return request.get('/api/v1/experiences')
}

/**
 * 获取业务履历详情
 */
export function getExperience(experienceId: number): Promise<Experience> {
  return request.get(`/api/v1/experiences/${experienceId}`)
}

/**
 * 更新业务履历
 */
export function updateExperience(experienceId: number, data: ExperienceUpdate): Promise<Experience> {
  return request.put(`/api/v1/experiences/${experienceId}`, data)
}

/**
 * 删除业务履历
 */
export function deleteExperience(experienceId: number): Promise<void> {
  return request.delete(`/api/v1/experiences/${experienceId}`)
}
