import http from './http'
import type { PageData } from './entries'

export interface KnowledgeTag {
  id: number
  name: string
}

export interface KnowledgeItem {
  id: number
  title: string
  summary: string | null
  category_id: number
  category_name: string
  knowledge_type: string
  source_dept: string
  keywords: string
  status: number
  status_label: string
  visibility: number
  view_count: number
  author_id: number
  publish_at: string | null
  created_at: string
  updated_at: string
  tags: KnowledgeTag[]
}

export interface KnowledgeDetail extends KnowledgeItem {
  content: string | null
}

export interface KnowledgeStats {
  total: number
  published: number
  draft: number
  offline: number
  month_new: number
  total_views: number
  by_type: Record<string, number>
  by_dept: Record<string, number>
}

export interface CategoryOption {
  id: number
  name: string
  level: number
  path: string
}

export interface KnowledgeOptions {
  knowledge_types: string[]
  statuses: Record<string, string>
  categories: CategoryOption[]
}

export interface KnowledgeQuery {
  keyword?: string
  knowledge_type?: string
  category_id?: number
  status?: number
  page?: number
  page_size?: number
}

export interface KnowledgePayload {
  title: string
  category_id: number
  knowledge_type: string
  summary?: string | null
  content?: string | null
  source_dept?: string | null
  keywords?: string | null
  status: number
  visibility?: number
}

export function getKnowledgeOptions(): Promise<KnowledgeOptions> {
  return http.get('/knowledge/options')
}

export function getKnowledgeStats(): Promise<KnowledgeStats> {
  return http.get('/knowledge/stats')
}

export function listKnowledge(query: KnowledgeQuery): Promise<PageData<KnowledgeItem>> {
  return http.get('/knowledge', { params: query })
}

export function getKnowledge(id: number): Promise<KnowledgeDetail> {
  return http.get(`/knowledge/${id}`)
}

export function createKnowledge(data: KnowledgePayload): Promise<KnowledgeDetail> {
  return http.post('/knowledge', data)
}

export function updateKnowledge(id: number, data: Partial<KnowledgePayload>): Promise<KnowledgeDetail> {
  return http.put(`/knowledge/${id}`, data)
}

export function changeKnowledgeStatus(id: number, status: number): Promise<KnowledgeItem> {
  return http.post(`/knowledge/${id}/status`, null, { params: { status } })
}

export function deleteKnowledge(id: number): Promise<unknown> {
  return http.delete(`/knowledge/${id}`)
}

// CSV 下载走 blob，避免直接把 token 暴露在 URL 上
export async function exportKnowledge(query: { knowledge_type?: string; status?: number } = {}): Promise<void> {
  const blob = (await http.get('/knowledge/export', {
    params: query,
    responseType: 'blob',
    timeout: 60000,
  })) as unknown as Blob
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '知识清单.csv'
  a.click()
  URL.revokeObjectURL(url)
}
