import http from './http'
import type { PageData } from './entries'

export interface KbService {
  id: number
  svc_code: string
  svc_name: string
  provider_dept: string | null
  svc_type: string // API/图谱/匹配/订阅/工具/交换
  description: string | null
  tags: string | null // 逗号分隔
  call_count: number
  api_count: number
  doc_version: string | null
  doc_url: string | null
  status: number // 1=已上架 0=已下架
  sort_order: number
  created_at: string
  updated_at: string
}

export interface ServiceOptions {
  svc_types: string[]
  statuses: { value: number; label: string }[]
}

export interface ServiceStats {
  total: number
  online: number
  month_new: number
  total_calls: number
  by_type: Record<string, number>
}

export interface ServiceQuery {
  keyword?: string
  svc_type?: string
  status?: number
  page?: number
  page_size?: number
}

export interface ServicePayload {
  svc_code?: string | null
  svc_name: string
  provider_dept?: string | null
  svc_type: string
  description?: string | null
  tags?: string | null
  api_count?: number
  doc_version?: string | null
  doc_url?: string | null
  status?: number
}

export interface ServiceApplyPayload {
  service_id: number
  apply_dept: string
  contact?: string | null
  reason?: string | null
}

export interface ServiceApplyResult {
  ticket: string
  svc_code: string
  svc_name: string
  apply_dept: string
  contact: string | null
  message: string
}

export function getServiceOptions(): Promise<ServiceOptions> {
  return http.get('/services/options')
}

export function getServiceStats(): Promise<ServiceStats> {
  return http.get('/services/stats')
}

export function listServices(query: ServiceQuery): Promise<PageData<KbService>> {
  return http.get('/services', { params: query })
}

export function createService(data: ServicePayload): Promise<KbService> {
  return http.post('/services', data)
}

export function updateService(id: number, data: Partial<ServicePayload>): Promise<KbService> {
  return http.put(`/services/${id}`, data)
}

export function deleteService(id: number): Promise<unknown> {
  return http.delete(`/services/${id}`)
}

export function toggleService(id: number): Promise<KbService> {
  return http.post(`/services/${id}/toggle`)
}

export function applyService(data: ServiceApplyPayload): Promise<ServiceApplyResult> {
  return http.post('/services/apply', data)
}
