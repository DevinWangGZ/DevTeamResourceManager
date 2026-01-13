/**
 * 用户管理API
 */
import request from './index'
import type { UserInfo } from './auth'

export interface UserUpdate {
  full_name?: string
  status_tag?: string
}

/**
 * 更新当前用户信息
 */
export function updateUser(data: UserUpdate): Promise<UserInfo> {
  return request.put('/api/v1/users/me', data)
}
