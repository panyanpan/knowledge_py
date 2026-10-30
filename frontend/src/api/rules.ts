import http from './http'
import type { PageData } from './entries'

export interface KbRule {
  id: number
  rule_code: string
  rule_name: string
  description: string | null
  rule_type: string
  scope_text: string | null
  condition_text: string | null
  hit_count: number
  run_count: number
  last_run_at: string | null
  status: number // 1=启用 0=停用 2=待复核
  sort_order: number
  created_at: string
  updated_at: string
}

export interface RuleOptions {
  rule_types: string[]
  statuses: { value: number; label: string }[]
}

export interface RuleQuery {
  keyword?: string
  rule_type?: string
  status?: number
  page?: number
  page_size?: number
}

export interface RulePayload {
  rule_code?: string | null
  rule_name: string
  description?: string | null
  rule_type: string
  scope_text?: string | null
  condition_text?: string | null
  status?: number
}

export interface RuleRunResult {
  rule_code: string
  rule_name: string
  scanned: number
  hits: number
  ran_at: string
  message: string
}

export function getRuleOptions(): Promise<RuleOptions> {
  return http.get('/rules/options')
}

export function listRules(query: RuleQuery): Promise<PageData<KbRule>> {
  return http.get('/rules', { params: query })
}

export function createRule(data: RulePayload): Promise<KbRule> {
  return http.post('/rules', data)
}

export function updateRule(id: number, data: Partial<RulePayload>): Promise<KbRule> {
  return http.put(`/rules/${id}`, data)
}

export function deleteRule(id: number): Promise<unknown> {
  return http.delete(`/rules/${id}`)
}

export function toggleRule(id: number): Promise<KbRule> {
  return http.post(`/rules/${id}/toggle`)
}

export function runRule(id: number): Promise<RuleRunResult> {
  return http.post(`/rules/${id}/run`)
}
