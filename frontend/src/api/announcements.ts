import http from './http'
import type { Announcement } from './portal'
import type { PageData } from './entries'

export interface AnnouncementPayload {
  type: number
  title: string
  content?: string | null
  image_url?: string | null
  link_url?: string | null
  sort_order?: number
  is_published?: number
}

export function listAnnouncements(params: {
  type?: number
  page?: number
  page_size?: number
}): Promise<PageData<Announcement>> {
  return http.get('/announcements', { params })
}

export function createAnnouncement(data: AnnouncementPayload): Promise<Announcement> {
  return http.post('/announcements', data)
}

export function updateAnnouncement(
  id: number,
  data: Partial<AnnouncementPayload>,
): Promise<Announcement> {
  return http.put(`/announcements/${id}`, data)
}

export function deleteAnnouncement(id: number): Promise<unknown> {
  return http.delete(`/announcements/${id}`)
}
