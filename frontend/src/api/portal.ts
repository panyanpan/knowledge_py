import http from './http'
import type { EntryBrief, EntryDetail, PageData } from './entries'

export interface Announcement {
  id: number
  type: number
  title: string
  content: string | null
  image_url: string | null
  link_url: string | null
  sort_order: number
  is_published: number
  created_at: string
}

export interface PortalCategory {
  id: number
  name: string
  level: number
  entry_count: number
  children: PortalCategory[]
}

export interface PortalHome {
  banners: Announcement[]
  notices: Announcement[]
  latest: EntryBrief[]
  hot: EntryBrief[]
  categories: PortalCategory[]
  stats: { public_entries: number }
}

export function getPortalHome(): Promise<PortalHome> {
  return http.get('/portal/home')
}

export function listPublicEntries(params: {
  keyword?: string
  category_id?: number
  page?: number
  page_size?: number
}): Promise<PageData<EntryBrief>> {
  return http.get('/portal/entries', { params })
}

export function getPublicEntry(id: number): Promise<EntryDetail> {
  return http.get(`/portal/entries/${id}`)
}
