import http from './http'
import type { PageData } from './entries'

export interface MetadataField {
  id: number
  field_name: string
  field_code: string
  data_type: string
  domain: string
  is_required: number
  status: number
  description: string | null
  rule_type: string | null
  rule_config: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface MetadataStats {
  total: number
  enabled: number
  disabled: number
  required: number
  pending: number
  domains: Record<string, number>
}

export interface MetadataOptions {
  data_types: string[]
  domains: string[]
  rule_types: string[]
}

export interface RuleCheckResult {
  passed: boolean
  issues: string[]
  message: string
}

export interface MetadataQuery {
  keyword?: string
  domain?: string
  status?: number
  data_type?: string
  page?: number
  page_size?: number
}

export interface MetadataPayload {
  field_name: string
  field_code: string
  data_type: string
  domain: string
  is_required: number
  status: number
  description?: string | null
  rule_type?: string | null
  rule_config?: string | null
  sort_order?: number
}

export function getOptions(): Promise<MetadataOptions> {
  return http.get('/metadata/options')
}

export function getStats(): Promise<MetadataStats> {
  return http.get('/metadata/stats')
}

export function listFields(query: MetadataQuery): Promise<PageData<MetadataField>> {
  return http.get('/metadata/fields', { params: query })
}

export function createField(data: MetadataPayload): Promise<MetadataField> {
  return http.post('/metadata/fields', data)
}

export function updateField(id: number, data: Partial<MetadataPayload>): Promise<MetadataField> {
  return http.put(`/metadata/fields/${id}`, data)
}

export function deleteField(id: number): Promise<unknown> {
  return http.delete(`/metadata/fields/${id}`)
}

export function checkRule(id: number): Promise<RuleCheckResult> {
  return http.post(`/metadata/fields/${id}/check-rule`)
}

// CSV 下载走 blob，避免直接暴露 token 到 URL
export async function exportFields(domain?: string): Promise<void> {
  const blob = (await http.get('/metadata/fields/export', {
    params: domain ? { domain } : {},
    responseType: 'blob',
    timeout: 60000,
  })) as Blob
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '知识元数据字段清单.csv'
  a.click()
  URL.revokeObjectURL(url)
}
