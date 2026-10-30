import http from './http'

export interface TraceNode {
  id: number
  step_no: number
  name: string
  sub: string
  occurred_at: string | null
  actor: string
  source_ref: string
  result: string
  result_level: 'green' | 'blue' | 'warn'
  evidence: string | null
}

export interface KbTrace {
  id: number
  trace_no: string
  title: string
  entry_no: string
  scene: string
  category: string
  version: string
  dept: string
  secret_level: string // 公开/内部/涉密
  chain_status: number // 1=完整可溯源 0=缺失待补录
  query_count: number
  last_query_at: string | null
  nodes?: TraceNode[]
}

export interface TraceOptions {
  chips: { id: number; title: string }[]
  secret_levels: string[]
  chain_status: { value: number; label: string }[]
}

export interface TraceStats {
  managed_entries: number
  chain_complete: number
  chain_missing: number
  queries_30d: number
}

export function getTraceOptions(): Promise<TraceOptions> {
  return http.get('/traces/options')
}

export function getTraceStats(): Promise<TraceStats> {
  return http.get('/traces/stats')
}

export function listTraces(keyword?: string): Promise<{ list: KbTrace[]; total: number }> {
  return http.get('/traces', { params: keyword ? { keyword } : {} })
}

export function getTraceDetail(id: number): Promise<KbTrace> {
  return http.get(`/traces/${id}`)
}

export function runTrace(id: number): Promise<KbTrace> {
  return http.post(`/traces/${id}/run`)
}
