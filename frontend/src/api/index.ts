import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
  responseEncoding: 'utf8',
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 如果是blob响应，返回整个response对象
    if (response.config.responseType === 'blob') {
      return response.data
    }
    return response.data
  },
  (error) => {
    // 统一错误处理
    const status = error.response?.status
    
    if (status === 401) {
      // Token过期或无效，清除token并跳转到登录页
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (status === 403) {
      // 权限不足
      console.error('权限不足:', error.response?.data?.detail || '无权限访问此资源')
    } else if (status === 404) {
      // 资源不存在
      console.error('资源不存在:', error.response?.data?.detail || '请求的资源不存在')
    } else if (status === 422) {
      // 请求参数验证失败
      console.error('参数验证失败:', error.response?.data)
    } else if (status >= 500) {
      // 服务器错误
      console.error('服务器错误:', error.response?.data?.detail || '服务器内部错误')
    } else if (!error.response) {
      // 网络错误
      console.error('网络错误:', '无法连接到服务器，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default request
