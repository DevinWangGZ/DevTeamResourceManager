import request from './index'

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  status_tag: string | null
  is_active: boolean
}

/**
 * 用户登录
 */
export const login = (data: LoginForm): Promise<TokenResponse> => {
  // OAuth2PasswordRequestForm 需要 form-urlencoded 格式
  const params = new URLSearchParams()
  params.append('username', data.username)
  params.append('password', data.password)
  
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    data: params,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

/**
 * 用户注册
 */
export const register = (data: RegisterForm): Promise<UserInfo> => {
  return request({
    url: '/api/v1/auth/register',
    method: 'post',
    data,
  })
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): Promise<UserInfo> => {
  return request({
    url: '/api/v1/auth/me',
    method: 'get',
  })
}
