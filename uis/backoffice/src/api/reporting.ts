import { request } from './client'

export interface WeeklyActivityRow {
  week_start: string
  week_end: string
  market: string
  local_id: string
  currency: string
  sales_total_amount: number | null
  ticket_count: number
  last_refreshed_at: string
  data_quality_status: string
}

export interface ReportingKpis {
  rows: WeeklyActivityRow[]
  count: number
  metric_kind: string
  data_quality_status: string
}

export interface ReportingStatus {
  status: string
  stale: boolean
  stale_after_days: number
  last_successful_run_at: string | null
}

export function getReportingKpis() {
  return request<ReportingKpis>('/reporting/kpis')
}

export function getReportingStatus() {
  return request<ReportingStatus>('/reporting/status')
}
