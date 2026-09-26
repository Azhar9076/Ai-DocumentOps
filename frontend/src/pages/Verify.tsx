import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowLeft,
  Calculator,
  Check,
  CheckCircle2,
  Download,
  MapPin,
  RefreshCw,
  RotateCw,
  Save,
  Sparkles,
  X,
} from 'lucide-react'
import { api, type DocumentDetail } from '../lib/api'
import { useAuth } from '../lib/authContext'
import { formatDateTime, useAsync } from '../lib/hooks'
import { ConfidenceTag, ErrorNotice, Panel, StatusBadge } from '../components/ui'

type Values = Record<string, string>

export function Verify() {
  const { documentId = '' } = useParams()
  const navigate = useNavigate()
  const { userEmail } = useAuth()
  const { data, error, loading, reload, setData } = useAsync(
    () => api.document(documentId),
    [documentId],
  )
  const [values, setValues] = useState<Values>({})
  const [focused, setFocused] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [reprocessing, setReprocessing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [banner, setBanner] = useState<string | null>(null)

  useEffect(() => {
    if (data) {
      setValues(Object.fromEntries(data.fields.map((f) => [f.field_key, f.field_value])))
    }
  }, [data])

  const failingFields = useMemo(() => {
    const keys = new Set<string>()
    data?.validation_issues.forEach((issue) => issue.fields.forEach((key) => keys.add(key)))
    return keys
  }, [data])

  const edits = useMemo(() => {
    if (!data) return []
    return data.fields
      .filter(
        (field) =>
          values[field.field_key] !== undefined && values[field.field_key] !== field.field_value,
      )
      .map((field) => ({ field_key: field.field_key, field_value: values[field.field_key] }))
  }, [data, values])

  // Live client-side math recalculation for invoice fields
  const liveMathCheck = useMemo(() => {
    if (data?.doc_type !== 'INVOICE') return null
    const subtotal = parseFloat((values.subtotal ?? '').replace(/[^0-9.-]+/g, ''))
    const tax = parseFloat((values.tax_amount ?? '').replace(/[^0-9.-]+/g, ''))
    const total = parseFloat((values.total_amount ?? '').replace(/[^0-9.-]+/g, ''))

    if (isNaN(subtotal) || isNaN(tax) || isNaN(total)) return null
    const expected = parseFloat((subtotal + tax).toFixed(2))
    const diff = Math.abs(expected - total)
    const valid = diff < 0.02

    return {
      subtotal,
      tax,
      total,
      expected,
      diff: parseFloat(diff.toFixed(2)),
      valid,
    }
  }, [data, values])

  // Detect self-correction attempt from audit logs
  const selfCorrectionAudit = useMemo(() => {
    if (!data) return null
    return data.audit_logs.find((log) => log.action === 'SELF_CORRECTION_ATTEMPT_2')
  }, [data])

  if (error) return <ErrorNotice error={error} onRetry={reload} />
  if (loading || !data) return <p className="p-6 text-sm text-ink-500">Loading document…</p>

  const isImage = data.mime_type.startsWith('image/')
  const isPdf = data.mime_type === 'application/pdf'
  const decided = data.status === 'APPROVED' || data.status === 'REJECTED'

  async function submit(decision: 'APPROVE' | 'REJECT', payloadEdits: typeof edits) {
    setSubmitting(true)
    setActionError(null)
    try {
      const updated: DocumentDetail = await api.review(documentId, {
        edits: payloadEdits,
        decision,
        reviewer_id: userEmail,
      })
      setData(updated)
      setBanner(decision === 'APPROVE' ? 'Document approved and saved.' : 'Document rejected.')
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleReprocess() {
    setReprocessing(true)
    setActionError(null)
    try {
      const updated: DocumentDetail = await api.reprocess(documentId)
      setData(updated)
      setBanner('Pipeline successfully reprocessed with latest agent models.')
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setReprocessing(false)
    }
  }

  async function handleApproveAndLearn(fieldKey: string) {
    const correctedValue = values[fieldKey] ?? ''
    setSubmitting(true)
    setActionError(null)
    try {
      const res = await api.correct(documentId, {
        field_name: fieldKey,
        corrected_value: correctedValue,
        reviewer_id: userEmail,
      })
      setData(res.document)
      setBanner(`Field '${fieldKey}' updated and saved to ground-truth benchmark cache for active learning.`)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  const focusedFieldObj = data.fields.find((f) => f.field_key === focused)

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold tracking-tight">{data.filename}</h1>
          <p className="text-xs text-ink-500">
            {data.doc_type} · uploaded {formatDateTime(data.uploaded_at)} · {data.processing_ms} ms latency
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-secondary text-xs"
            disabled={reprocessing}
            onClick={handleReprocess}
            title="Re-run entire sequential agent pipeline"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${reprocessing ? 'animate-spin' : ''}`} />
            Reprocess
          </button>
          <a
            href={api.auditExportUrl(data.id, 'pdf')}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary text-xs bg-ink-900 text-white hover:bg-ink-800"
            title="Download official Compliance & Audit Certificate PDF"
          >
            <Download className="h-3.5 w-3.5" /> Audit PDF
          </a>
          <a
            href={api.exportUrl(data.id, 'json')}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary text-xs"
            title="Export full JSON extraction"
          >
            <Download className="h-3.5 w-3.5" /> JSON
          </a>
          <a
            href={api.exportUrl(data.id, 'csv')}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary text-xs"
            title="Export CSV audit report"
          >
            <Download className="h-3.5 w-3.5" /> CSV
          </a>
        </div>

        <ConfidenceTag score={data.overall_confidence} />
        <StatusBadge status={data.status} />
      </header>

      {/* AI Compliance Auditor Summary Banner */}
      {data.audit_summary && (
        <div className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50/90 p-4 text-xs leading-relaxed text-sky-950 shadow-sm">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-sky-600" />
          <div className="flex-1">
            <span className="font-semibold uppercase tracking-wider text-sky-800">
              AI Compliance Auditor Summary:
            </span>{' '}
            {data.audit_summary}
          </div>
        </div>
      )}

      {/* Self-Correction Loop Banner */}
      {selfCorrectionAudit && (
        <div className="flex items-start gap-2.5 rounded-xl border border-purple-200 bg-purple-50/90 px-4 py-3 text-xs text-purple-900">
          <RotateCw className="mt-0.5 h-4 w-4 shrink-0 text-purple-600" />
          <div>
            <span className="font-semibold">Self-Correction Feedback Loop Triggered:</span> Initial math check failed. Extractor Agent re-attempted and refined parameters automatically.
          </div>
        </div>
      )}

      {banner && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-800">
          {banner} <Link to="/queue" className="font-medium underline ml-1">Back to queue</Link>
        </div>
      )}
      {actionError && <ErrorNotice error={actionError} />}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Document Viewer & Explainability Highlighting */}
        <Panel title="Document &amp; Layout Grounding" className="xl:sticky xl:top-6 xl:self-start">
          <div className="overflow-hidden rounded-xl border border-ink-200 bg-white">
            {isPdf && (
              <object data={api.fileUrl(data.id)} type="application/pdf" className="h-[68vh] w-full">
                <p className="p-4 text-sm text-ink-500">
                  Inline PDF preview unavailable.{' '}
                  <a className="underline" href={api.fileUrl(data.id)} target="_blank" rel="noreferrer">
                    Open file
                  </a>
                  .
                </p>
              </object>
            )}
            {isImage && (
              <img src={api.fileUrl(data.id)} alt={data.filename} className="max-h-[68vh] w-full object-contain" />
            )}
            {!isPdf && !isImage && (
              <div className="max-h-[68vh] overflow-auto p-4">
                <pre className="whitespace-pre-wrap text-xs font-mono text-ink-800">
                  {data.raw_text}
                </pre>
              </div>
            )}
          </div>

          {/* Section 7 & 14.1: Explainability Anchor Inspector */}
          <div className="mt-3">
            {focused ? (
              <div className="flex items-center justify-between rounded-lg border border-sky-200 bg-sky-50/90 px-3.5 py-2.5 text-xs text-sky-900">
                <div className="flex items-center gap-2">
                  <MapPin className="h-3.5 w-3.5 text-sky-600" />
                  <span>
                    Focusing field: <span className="font-semibold">{focused}</span>
                  </span>
                </div>
                {focusedFieldObj?.bbox ? (
                  <span className="rounded bg-sky-200/70 px-2 py-0.5 font-mono text-[11px] text-sky-900">
                    Pos: {focusedFieldObj.bbox}
                  </span>
                ) : (
                  <span className="rounded bg-amber-100 px-2 py-0.5 text-[11px] text-amber-800">
                    Location anchor unavailable
                  </span>
                )}
              </div>
            ) : (
              <p className="text-[11px] text-ink-500">
                Tip: Click or focus on any extracted field to inspect its visual grounding coordinates.
              </p>
            )}
          </div>
        </Panel>

        {/* Extracted Fields & Review Interface */}
        <div className="space-y-5">
          {data.validation_issues.length > 0 && (
            <div className="space-y-2">
              {data.validation_issues.map((issue) => (
                <div
                  key={`${issue.rule}-${issue.message}`}
                  className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-xs ${
                    issue.severity === 'error'
                      ? 'border-rose-200 bg-rose-50/90 text-rose-800'
                      : 'border-amber-200 bg-amber-50/90 text-amber-800'
                  }`}
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-semibold capitalize">{issue.rule.replace(/_/g, ' ')}</p>
                    <p className="mt-0.5">{issue.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Section 5: Real-time Live Math Engine Validator Card */}
          {liveMathCheck && (
            <div
              className={`flex items-center justify-between rounded-xl border px-4 py-3 text-xs transition ${
                liveMathCheck.valid
                  ? 'border-emerald-200 bg-emerald-50/90 text-emerald-900'
                  : 'border-rose-200 bg-rose-50/90 text-rose-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Calculator className="h-4 w-4" />
                <span>
                  Live Math Audit: Subtotal (${liveMathCheck.subtotal.toFixed(2)}) + Tax ($
                  {liveMathCheck.tax.toFixed(2)}) ={' '}
                  <span className="font-semibold">${liveMathCheck.expected.toFixed(2)}</span>
                  {' vs '}
                  Stated Total: <span className="font-semibold">${liveMathCheck.total.toFixed(2)}</span>
                </span>
              </div>
              {liveMathCheck.valid ? (
                <span className="inline-flex items-center gap-1 rounded bg-emerald-200/70 px-2 py-0.5 font-medium text-emerald-800">
                  <CheckCircle2 className="h-3 w-3" /> Balanced
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded bg-rose-200/70 px-2 py-0.5 font-medium text-rose-800">
                  <AlertTriangle className="h-3 w-3" /> Δ ${liveMathCheck.diff.toFixed(2)}
                </span>
              )}
            </div>
          )}

          <Panel title="Extracted Fields (IBM Granite 3.0)">
            <div className="space-y-3">
              {data.fields.map((field) => {
                const failing = failingFields.has(field.field_key)
                const isLowConfidence = field.confidence_score < 0.80
                return (
                  <div
                    key={field.id}
                    className={`rounded-xl border p-3 transition ${
                      focused === field.field_key
                        ? 'border-sky-400 bg-sky-50/70 shadow-sm'
                        : failing
                          ? 'border-rose-200 bg-rose-50/40'
                          : isLowConfidence
                            ? 'border-amber-200 bg-amber-50/30'
                            : 'border-ink-200 bg-white/60'
                    }`}
                  >
                    <div className="mb-1.5 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <label
                          htmlFor={`field-${field.id}`}
                          className="text-xs font-semibold uppercase tracking-wide text-ink-600"
                        >
                          {field.field_key.replace(/_/g, ' ')}
                        </label>
                        {isLowConfidence && (
                          <span className="rounded bg-amber-100 px-1.5 py-0.2 text-[10px] font-medium text-amber-800">
                            Low Confidence
                          </span>
                        )}
                        {values[field.field_key] !== undefined &&
                          values[field.field_key] !== field.field_value && (
                            <span className="rounded bg-purple-100 px-1.5 py-0.2 text-[10px] font-semibold text-purple-800">
                              Modified
                            </span>
                          )}
                      </div>
                      <div className="flex items-center gap-2">
                        {values[field.field_key] !== undefined &&
                          values[field.field_key] !== field.field_value && (
                            <button
                              type="button"
                              onClick={() => void handleApproveAndLearn(field.field_key)}
                              disabled={submitting || decided}
                              className="inline-flex items-center gap-1 rounded bg-purple-600 px-2 py-0.5 text-[11px] font-medium text-white hover:bg-purple-700 transition shadow-sm"
                              title="Update field and feed active-learning ground truth cache"
                            >
                              <Sparkles className="h-3 w-3" /> Approve &amp; Learn
                            </button>
                          )}
                        <ConfidenceTag score={field.confidence_score} />
                      </div>
                    </div>
                    <input
                      id={`field-${field.id}`}
                      className="input-base text-sm"
                      value={values[field.field_key] ?? ''}
                      disabled={decided}
                      onFocus={() => setFocused(field.field_key)}
                      onChange={(event) =>
                        setValues((current) => ({
                          ...current,
                          [field.field_key]: event.target.value,
                        }))
                      }
                    />
                  </div>
                )
              })}
              {data.fields.length === 0 && (
                <p className="py-6 text-center text-sm text-ink-500">
                  No fields were extracted from this document.
                </p>
              )}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-primary"
                disabled={submitting || decided}
                onClick={() => void submit('APPROVE', [])}
              >
                <Check className="h-4 w-4" /> Approve Data
              </button>
              <button
                type="button"
                className="btn-secondary"
                disabled={submitting || decided || edits.length === 0}
                onClick={() => void submit('APPROVE', edits)}
              >
                <Save className="h-4 w-4" /> Save Edits &amp; Approve
                {edits.length > 0 && (
                  <span className="rounded-md bg-ink-900 px-1.5 py-0.5 text-[11px] text-white">
                    {edits.length}
                  </span>
                )}
              </button>
              <button
                type="button"
                className="btn-danger"
                disabled={submitting || decided}
                onClick={() => void submit('REJECT', [])}
              >
                <X className="h-4 w-4" /> Reject Document
              </button>
            </div>
          </Panel>

          {/* Audit Trail & Lineage */}
          <Panel title="System Audit Lineage">
            <ol className="space-y-2.5">
              {data.audit_logs.map((log) => (
                <li key={log.id} className="flex gap-3 text-xs">
                  <span className="w-24 shrink-0 text-ink-400 font-mono text-[11px]">
                    {formatDateTime(log.timestamp)}
                  </span>
                  <span className="w-44 shrink-0 font-medium text-ink-900">{log.action}</span>
                  <span className="min-w-0 flex-1 truncate text-ink-600 font-mono text-[11px]" title={log.details}>
                    {log.details}
                  </span>
                  <span className="shrink-0 text-ink-400 text-[11px]">{log.performed_by}</span>
                </li>
              ))}
            </ol>
          </Panel>
        </div>
      </div>
    </div>
  )
}
