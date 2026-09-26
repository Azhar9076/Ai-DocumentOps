const getFallbackApiBase = (): string => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return 'https://ai-documentops-2.onrender.com'
  }
  return 'http://localhost:8000'
}

export const API_BASE = (import.meta.env.VITE_API_BASE || getFallbackApiBase()).replace(/\/$/, '')

export type DocStatus =
  | 'UPLOADED'
  | 'PROCESSING'
  | 'AUTO_APPROVED'
  | 'NEEDS_REVIEW'
  | 'ACTION_REQUIRED'
  | 'APPROVED'
  | 'REJECTED'
  | 'FAILED'
  | 'CANCELLED'

export type DocType = 'INVOICE' | 'FORM' | 'CONTRACT' | 'UNKNOWN'

export interface ExtractedFieldDto {
  id: string
  field_key: string
  field_value: string
  confidence_score: number
  is_validated: boolean
  bbox: string | null
}

export interface ValidationIssue {
  rule: string
  message: string
  severity: string
  fields: string[]
}

export interface AuditLogDto {
  id: string
  action: string
  performed_by: string
  timestamp: string
  details: string
}

export interface ReviewDto {
  id: string
  field_key: string
  original_value: string
  corrected_value: string
  reviewer_id: string
  reviewed_at: string
}

export interface DocumentSummary {
  id: string
  filename: string
  doc_type: DocType
  status: DocStatus
  overall_confidence: number
  uploaded_at: string
  processing_ms: number
  audit_summary?: string
}

export interface DocumentDetail extends DocumentSummary {
  file_path: string
  mime_type: string
  page_count: number
  raw_text: string
  audit_summary: string
  fields: ExtractedFieldDto[]
  reviews: ReviewDto[]
  audit_logs: AuditLogDto[]
  validation_issues: ValidationIssue[]
}

export interface RoiMetrics {
  hours_saved_per_100_docs?: number
  math_errors_intercepted_pct?: number
  straight_through_rate?: number
  cost_reduction_est?: string
}

export interface Metrics {
  documents_processed: number
  auto_automation_rate: number
  reviews_pending: number
  average_confidence: number
  estimated_hours_saved: number
  math_errors_intercepted: number
  status_breakdown: Record<string, number>
  confidence_distribution: { bucket: string; count: number }[]
  accuracy_trend: { date: string; confidence: number; documents: number }[]
  roi_metrics: RoiMetrics
}

export interface CalibrationItem {
  bucket: string
  expected_accuracy: string
  actual_accuracy: number
  count: number
}

export interface AccuracyIteration {
  iteration: number
  timestamp: string
  field_accuracy: number
  routing_accuracy: number
  avg_latency_ms: number
}

export interface PromptVersionData {
  field_accuracy: number
  routing_accuracy: number
  label: string
}

export interface V1Comparison {
  prompt_v1: PromptVersionData
  prompt_v2: PromptVersionData
  delta: {
    field_accuracy_lift: number
    routing_accuracy_lift: number
  }
}

export interface RoutingThresholds {
  auto_approved_min: number
  needs_review_min: number
}

export interface StressTestResponse {
  job_ids: string[]
  started: number
  budget_remaining: number
  max_calls: number
}

export interface Quality {
  overall_accuracy: number
  routing_accuracy: number
  field_accuracy: { field_key: string; accuracy: number; samples: number }[]
  math_validation_pass_rate: number
  human_correction_rate: number
  confidence_calibration: CalibrationItem[]
  accuracy_iterations: AccuracyIteration[]
  roi_metrics: RoiMetrics
  sample_size: number
  notice: string
  v1_comparison?: V1Comparison | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body?.detail) detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export const api = {
  metrics: () => request<Metrics>('/api/metrics'),
  quality: (refresh: boolean = false, compare: boolean = false) => {
    const params = new URLSearchParams()
    if (refresh) params.append('refresh', 'true')
    if (compare) params.append('compare', 'true')
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<Quality>(`/api/quality${qs}`)
  },
  triggerBenchmark: () => request<Quality>('/api/quality/benchmark', { method: 'POST' }),
  documents: (status?: DocStatus) =>
    request<DocumentSummary[]>(`/api/documents${status ? `?status=${status}` : ''}`),
  document: (id: string) => request<DocumentDetail>(`/api/documents/${id}`),
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<DocumentDetail>('/api/documents', { method: 'POST', body })
  },
  cancel: (id: string) =>
    request<DocumentDetail>(`/api/documents/${id}/cancel`, { method: 'POST' }),
  reprocess: (id: string) =>
    request<DocumentDetail>(`/api/documents/${id}/reprocess`, { method: 'POST' }),
  correct: (
    id: string,
    payload: {
      field_name: string
      corrected_value: string
      reviewer_id?: string
    },
  ) =>
    request<{ status: string; math_result: any; document: DocumentDetail }>(
      `/api/documents/${id}/correct`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    ),
  review: (
    id: string,
    payload: {
      edits: { field_key: string; field_value: string }[]
      decision: 'APPROVE' | 'REJECT'
      reviewer_id?: string
      note?: string
    },
  ) =>
    request<DocumentDetail>(`/api/documents/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  bulkReview: (payload: { document_ids: string[]; decision: 'APPROVE' | 'REJECT'; reviewer_id?: string }) =>
    request<DocumentSummary[]>('/api/documents/bulk-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  getThresholds: () => request<RoutingThresholds>('/api/admin/thresholds'),
  updateThresholds: (thresholds: RoutingThresholds) =>
    request<RoutingThresholds>('/api/admin/thresholds', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(thresholds),
    }),
  stressTest: (sampleCount: number = 5) =>
    request<StressTestResponse>(`/api/demo/stress-test?sample_count=${sampleCount}`, {
      method: 'POST',
    }),
  stressTestStatus: (jobIds: string[] = []) =>
    request<DocumentSummary[]>(
      `/api/demo/stress-test/status${jobIds.length ? `?job_ids=${jobIds.join(',')}` : ''}`,
    ),
  fileUrl: (id: string) => `${API_BASE}/api/documents/${id}/file`,
  exportUrl: (id: string, format: 'json' | 'csv' = 'json') =>
    `${API_BASE}/api/documents/${id}/export?format=${format}`,
  auditExportUrl: (id: string, format: 'pdf' | 'csv' = 'pdf') =>
    `${API_BASE}/api/documents/${id}/export-audit?format=${format}`,
}
