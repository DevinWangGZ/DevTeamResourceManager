/**
 * 错误处理工具
 */
export interface ApiError {
  detail: string
  code?: string
  errors?: Array<{
    field: string
    message: string
  }>
}

/**
 * 从API错误中提取错误消息
 */
export function getErrorMessage(error: any): string {
  if (error?.response?.data) {
    const data = error.response.data
    if (data.detail) {
      return data.detail
    }
    if (data.message) {
      return data.message
    }
  }
  if (error?.message) {
    return error.message
  }
  return '请求失败，请稍后重试'
}

/**
 * 获取错误码
 */
export function getErrorCode(error: any): string | undefined {
  return error?.response?.data?.code
}

/**
 * 判断是否为网络错误
 */
export function isNetworkError(error: any): boolean {
  return !error?.response && error?.request
}

/**
 * 判断是否为认证错误
 */
export function isAuthError(error: any): boolean {
  return error?.response?.status === 401
}

/**
 * 判断是否为权限错误
 */
export function isPermissionError(error: any): boolean {
  return error?.response?.status === 403
}
