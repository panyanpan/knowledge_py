import http from './http'
import type { Tag } from './tags'

export interface Attachment {
  id: number
  file_name: string
  file_size: number
  mime_type: string
}

export interface EntryBrief {
  id: number
  category_id: number
  author_id: number
  title: string
  summary: string | null
  visibility: number
  view_count: number
  created_at: string
  tags: Tag[]
}

export interface EntryDetail extends EntryBrief {
  content: string | null
  attachments: Attachment[]
}

export interface PageData<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

export interface EntryQuery {
  keyword?: string
  category_id?: number
  visibility?: number
  page?: number
  page_size?: number
}

export interface EntryPayload {
  category_id: number
  title: string
  content?: string | null
  summary?: string | null
  visibility: number
  tag_ids: number[]
}

export function listEntries(query: EntryQuery): Promise<PageData<EntryBrief>> {
  return http.get('/entries', { params: query })
}

export function getEntry(id: number): Promise<EntryDetail> {
  return http.get(`/entries/${id}`)
}

export function createEntry(data: EntryPayload): Promise<EntryDetail> {
  return http.post('/entries', data)
}

export function updateEntry(id: number, data: Partial<EntryPayload>): Promise<EntryDetail> {
  return http.put(`/entries/${id}`, data)
}

export function deleteEntry(id: number): Promise<unknown> {
  return http.delete(`/entries/${id}`)
}
