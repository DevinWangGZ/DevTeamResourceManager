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

/**
 * 上传附件（Word、PPT、PDF、Excel）
 */
export interface AttachmentUploadResponse {
  url: string
  filename: string
  saved_filename: string
  size: number
  type: string
  mime_type: string
}

export function uploadAttachment(file: File): Promise<AttachmentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/v1/upload/attachment', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
