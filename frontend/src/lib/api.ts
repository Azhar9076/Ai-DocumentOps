export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export type DocStatus =
  | 'UPLOADED'
  | 'PROCESSING'
  | 'AUTO_APPROVED'
  | 'NEEDS_REVIEW'
  | 'ACTION_REQUIRED'
  | 'APPROVED'
  | 'REJECTED'
  | 'FAILED'

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
}

export interface DocumentDetail extends DocumentSummary {
  file_path: string
  mime_type: string
  page_count: number
  raw_text: string
  fields: ExtractedFieldDto[]
  reviews: ReviewDto[]
  audit_logs: AuditLogDto[]
  validation_issues: ValidationIssue[]
}

export interface Metrics {
  documents_processed: number
  auto_automation_rate: number
  reviews_pending: number
  average_confidence: number
  estimated_hours_saved: number
  status_breakdown: Record<string, number>
  confidence_distribution: { bucket: string; count: number }[]
  accuracy_trend: { date: string; confidence: number; documents: number }[]
}

export interface Quality {
  overall_accuracy: number
  field_accuracy: { field_key: string; accuracy: number; samples: number }[]
  math_validation_pass_rate: number
  human_correction_rate: number
  sample_size: number
  notice: string
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
  quality: () => request<Quality>('/api/quality'),
  documents: (status?: DocStatus) =>
    request<DocumentSummary[]>(`/api/documents${status ? `?status=${status}` : ''}`),
  document: (id: string) => request<DocumentDetail>(`/api/documents/${id}`),
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<DocumentDetail>('/api/documents', { method: 'POST', body })
  },
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
  fileUrl: (id: string) => `${API_BASE}/api/documents/${id}/file`,
}
