import request from './index'

export interface Message {
  id: number
  user_id: number
  title: string
  content?: string
  type: string
  is_read: boolean
  related_task_id?: number
  created_at: string
}

export interface MessageListResponse {
  total: number
  items: Message[]
}

export interface MessageUnreadCountResponse {
  unread_count: number
}

/**
 * 获取消息列表
 */
export function getMessages(params?: {
  type?: string
  is_read?: boolean
  page?: number
  page_size?: number
}): Promise<MessageListResponse> {
  return request.get('/api/v1/messages', { params })
}

/**
 * 获取未读消息数量
 */
export function getUnreadCount(): Promise<MessageUnreadCountResponse> {
  return request.get('/api/v1/messages/unread-count')
}

/**
 * 标记消息为已读
 */
export function markAsRead(messageId: number): Promise<Message> {
  return request.post(`/api/v1/messages/${messageId}/read`)
}

/**
 * 标记所有消息为已读
 */
export function markAllAsRead(type?: string): Promise<{ message: string }> {
  return request.post('/api/v1/messages/read-all', null, { params: type ? { type } : {} })
}

/**
 * 删除消息
 */
export function deleteMessage(messageId: number): Promise<void> {
  return request.delete(`/api/v1/messages/${messageId}`)
}
