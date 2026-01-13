/**
 * 用户序列管理API
 */
import request from './index'

export interface UserSequence {
  id: number
  user_id: number
  level: string
  unit_price: number
  created_at: string
  updated_at: string
}

export interface UserSequenceCreate {
  level: string
  unit_price: number
}

export interface UserSequenceUpdate {
  level?: string
  unit_price?: number
}

export interface UserSequenceListResponse {
  total: number
  items: UserSequence[]
}

/**
 * 创建用户序列
 */
export function createUserSequence(data: UserSequenceCreate): Promise<UserSequence> {
  return request.post('/api/v1/user-sequences', data)
}

/**
 * 获取用户序列列表
 */
export function getUserSequences(): Promise<UserSequenceListResponse> {
  return request.get('/api/v1/user-sequences')
}

/**
 * 获取用户序列详情
 */
export function getUserSequence(sequenceId: number): Promise<UserSequence> {
  return request.get(`/api/v1/user-sequences/${sequenceId}`)
}

/**
 * 更新用户序列
 */
export function updateUserSequence(sequenceId: number, data: UserSequenceUpdate): Promise<UserSequence> {
  return request.put(`/api/v1/user-sequences/${sequenceId}`, data)
}

/**
 * 删除用户序列
 */
export function deleteUserSequence(sequenceId: number): Promise<void> {
  return request.delete(`/api/v1/user-sequences/${sequenceId}`)
}
