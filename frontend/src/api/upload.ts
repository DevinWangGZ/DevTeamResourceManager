/**
 * 文件上传API
 */
import request from './index'

export interface ImageUploadResponse {
  url: string
  filename: string
  size: number
}

/**
 * 上传图片
 */
export function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return request.post('/api/v1/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
