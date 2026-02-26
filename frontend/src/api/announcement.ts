/**
 * 系统公告 API
 */
import request from './index'

export type AnnouncementPriority = 'normal' | 'important' | 'urgent'

export interface Announcement {
  id: number
  title: string
  content: string
  priority: AnnouncementPriority
  is_active: boolean
  author_id: number
  author_name?: string
  created_at: string
  updated_at: string
}

export interface AnnouncementListResponse {
  total: number
  items: Announcement[]
}

export interface AnnouncementCreateParams {
  title: string
  content: string
  priority: AnnouncementPriority
  is_active: boolean
}

export interface AnnouncementUpdateParams {
  title?: string
  content?: string
  priority?: AnnouncementPriority
  is_active?: boolean
}

/** 获取公告列表（所有用户）*/
export function getAnnouncements(includeInactive = false): Promise<AnnouncementListResponse> {
  return request.get('/api/v1/announcements', {
    params: includeInactive ? { include_inactive: true } : {},
  })
}

/** 创建公告（仅系统管理员）*/
export function createAnnouncement(data: AnnouncementCreateParams): Promise<Announcement> {
  return request.post('/api/v1/announcements', data)
}

/** 更新公告（仅系统管理员）*/
export function updateAnnouncement(id: number, data: AnnouncementUpdateParams): Promise<Announcement> {
  return request.put(`/api/v1/announcements/${id}`, data)
}

/** 删除公告（仅系统管理员）*/
export function deleteAnnouncement(id: number): Promise<void> {
  return request.delete(`/api/v1/announcements/${id}`)
}
