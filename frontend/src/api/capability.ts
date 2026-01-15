/**
 * 团队能力洞察API
 */
import request from './index'

export interface SkillMatrixDeveloper {
  user_id: number
  username: string
  full_name?: string
  sequence_level?: string
  skills: Record<string, string> // skill_name -> proficiency
}

export interface SkillMatrixResponse {
  skill_names: string[]
  developers: SkillMatrixDeveloper[]
}

export interface TalentLadderMember {
  user_id: number
  username: string
  full_name?: string
  sequence_level: string
  total_skills: number
  expert_skills: number
  proficient_skills: number
  familiar_skills: number
  total_man_days: number
}

export interface TalentLadderSummary {
  level: string
  count: number
  avg_skills: number
  avg_man_days: number
}

export interface TalentLadderResponse {
  ladder_summary: TalentLadderSummary[]
  ladder_data: Record<string, TalentLadderMember[]>
}

export interface CapabilityDistributionResponse {
  proficiency_distribution: {
    expert: number
    proficient: number
    familiar: number
  }
  sequence_distribution: Record<string, number>
  skill_count_distribution: {
    '0-5': number
    '6-10': number
    '11-15': number
    '16+': number
  }
  total_members: number
}

/**
 * 获取团队技能矩阵
 */
export function getSkillMatrix(): Promise<SkillMatrixResponse> {
  return request.get('/api/v1/capability/skill-matrix')
}

/**
 * 获取人才梯队分析
 */
export function getTalentLadder(): Promise<TalentLadderResponse> {
  return request.get('/api/v1/capability/talent-ladder')
}

/**
 * 获取团队能力分布
 */
export function getCapabilityDistribution(): Promise<CapabilityDistributionResponse> {
  return request.get('/api/v1/capability/capability-distribution')
}
