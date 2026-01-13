/**
 * 用户管理API
 */
import request from './index'
import type { UserInfo } from './auth'

export interface UserUpdate {
  full_name?: string
  status_tag?: string
}

export interface UserListResponse {
  total: number
  items: UserInfo[]
}

/**
 * 获取用户列表
 */
export function getUsers(params?: {
  skip?: number
  limit?: number
  role?: string
  is_active?: boolean
}): Promise<UserListResponse> {
  return request.get('/api/v1/users', { params })
}

/**
 * 更新当前用户信息
 */
export function updateUser(data: UserUpdate): Promise<UserInfo> {
  return request.put('/api/v1/users/me', data)
}
