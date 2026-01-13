import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, register as apiRegister, getCurrentUser, type UserInfo } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string>('')

  // 从localStorage恢复token
  const savedToken = localStorage.getItem('token')
  if (savedToken) {
    token.value = savedToken
  }

  /**
   * 设置token
   */
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  /**
   * 设置用户信息
   */
  const setUserInfo = (info: UserInfo) => {
    userInfo.value = info
  }

  /**
   * 登录
   */
  const login = async (username: string, password: string) => {
    try {
      const response = await apiLogin({ username, password })
      setToken(response.access_token)
      
      // 获取用户信息
      await fetchUserInfo()
      
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败，请检查用户名和密码',
      }
    }
  }

  /**
   * 注册
   */
  const register = async (username: string, email: string, password: string, fullName?: string) => {
    try {
      const user = await apiRegister({
        username,
        email,
        password,
        full_name: fullName,
      })
      
      // 注册成功后自动登录
      const loginResult = await login(username, password)
      return loginResult
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败',
      }
    }
  }

  /**
   * 获取用户信息
   */
  const fetchUserInfo = async () => {
    if (!token.value) {
      return
    }
    
    try {
      const info = await getCurrentUser()
      setUserInfo(info)
    } catch (error) {
      // token可能已过期，清除token
      logout()
    }
  }

  /**
   * 登出
   */
  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  /**
   * 检查是否已登录
   */
  const isLoggedIn = () => {
    return !!token.value
  }

  // 如果有token，尝试获取用户信息
  if (token.value) {
    fetchUserInfo()
  }

  return {
    userInfo,
    token,
    setToken,
    setUserInfo,
    login,
    register,
    fetchUserInfo,
    logout,
    isLoggedIn,
  }
})
