/**
 * 知识分享API
 */
import request from './index'

export interface Article {
  id: number
  title: string
  content: string
  author_id: number
  author_name?: string
  author_full_name?: string
  category?: string
  tags?: string
  is_published: boolean
  view_count: number
  created_at: string
  updated_at: string
}

export interface ArticleListResponse {
  total: number
  items: Article[]
}

export interface Category {
  name: string
  count: number
}

export interface Tag {
  name: string
  count: number
}

export interface ArticleCreateParams {
  title: string
  content: string
  category?: string
  tags?: string
  is_published?: boolean
}

export interface ArticleUpdateParams {
  title?: string
  content?: string
  category?: string
  tags?: string
  is_published?: boolean
}

/**
 * 获取文章列表
 */
export function getArticles(params?: {
  keyword?: string
  category?: string
  tag?: string
  author_id?: number
  is_published?: boolean
  page?: number
  page_size?: number
}): Promise<ArticleListResponse> {
  return request.get('/api/v1/articles', { params })
}

/**
 * 获取文章详情
 */
export function getArticle(articleId: number): Promise<Article> {
  return request.get(`/api/v1/articles/${articleId}`)
}

/**
 * 创建文章
 */
export function createArticle(data: ArticleCreateParams): Promise<Article> {
  return request.post('/api/v1/articles', data)
}

/**
 * 更新文章
 */
export function updateArticle(articleId: number, data: ArticleUpdateParams): Promise<Article> {
  return request.put(`/api/v1/articles/${articleId}`, data)
}

/**
 * 删除文章
 */
export function deleteArticle(articleId: number): Promise<void> {
  return request.delete(`/api/v1/articles/${articleId}`)
}

/**
 * 获取所有分类
 */
export function getCategories(): Promise<Category[]> {
  return request.get('/api/v1/articles/categories/list')
}

/**
 * 获取所有标签
 */
export function getTags(): Promise<Tag[]> {
  return request.get('/api/v1/articles/tags/list')
}

/**
 * 获取当前用户的文章列表
 */
export function getMyArticles(params?: {
  is_published?: boolean
  page?: number
  page_size?: number
}): Promise<ArticleListResponse> {
  return request.get('/api/v1/articles/my/articles', { params })
}
