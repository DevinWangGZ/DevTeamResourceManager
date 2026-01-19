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

/**
 * 创建用户（仅管理员）
 */
export interface UserCreateParams {
  username: string
  email: string
  full_name?: string
  role_codes?: string[]
  is_active?: boolean
}

export function createUser(data: UserCreateParams): Promise<UserInfo> {
  return request.post('/api/v1/users', data)
}

/**
 * 删除用户（仅管理员）
 */
export function deleteUser(userId: number): Promise<void> {
  return request.delete(`/api/v1/users/${userId}`)
}

/**
 * 更新用户信息（仅管理员）
 */
export function updateUserByAdmin(userId: number, data: UserUpdate & { is_active?: boolean }): Promise<UserInfo> {
  return request.put(`/api/v1/users/${userId}`, data)
}
