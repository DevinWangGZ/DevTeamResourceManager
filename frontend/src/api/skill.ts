/**
 * 技能管理API
 */
import request from './index'

export interface Skill {
  id: number
  user_id: number
  name: string
  proficiency: string
  created_at: string
  updated_at: string
}

export interface SkillCreate {
  name: string
  proficiency: 'familiar' | 'proficient' | 'expert'
}

export interface SkillUpdate {
  name?: string
  proficiency?: 'familiar' | 'proficient' | 'expert'
}

export interface SkillListResponse {
  total: number
  items: Skill[]
}

/**
 * 创建技能
 */
export function createSkill(data: SkillCreate): Promise<Skill> {
  return request.post('/api/v1/skills', data)
}

/**
 * 获取技能列表
 */
export function getSkills(): Promise<SkillListResponse> {
  return request.get('/api/v1/skills')
}

/**
 * 获取技能详情
 */
export function getSkill(skillId: number): Promise<Skill> {
  return request.get(`/api/v1/skills/${skillId}`)
}

/**
 * 更新技能
 */
export function updateSkill(skillId: number, data: SkillUpdate): Promise<Skill> {
  return request.put(`/api/v1/skills/${skillId}`, data)
}

/**
 * 删除技能
 */
export function deleteSkill(skillId: number): Promise<void> {
  return request.delete(`/api/v1/skills/${skillId}`)
}
