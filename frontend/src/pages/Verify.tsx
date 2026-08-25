import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { AlertTriangle, ArrowLeft, Check, FileText, Save, X } from 'lucide-react'
import { api, type DocumentDetail } from '../lib/api'
import { formatDateTime, useAsync } from '../lib/hooks'
import { ConfidenceTag, ErrorNotice, Panel, StatusBadge } from '../components/ui'

type Values = Record<string, string>

export function Verify() {
  const { documentId = '' } = useParams()
  const navigate = useNavigate()
  const { data, error, loading, reload, setData } = useAsync(
    () => api.document(documentId),
    [documentId],
  )
  const [values, setValues] = useState<Values>({})
  const [focused, setFocused] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
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
      .filter((field) => values[field.field_key] !== undefined && values[field.field_key] !== field.field_value)
      .map((field) => ({ field_key: field.field_key, field_value: values[field.field_key] }))
  }, [data, values])

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
      })
      setData(updated)
      setBanner(decision === 'APPROVE' ? 'Document approved and stored.' : 'Document rejected.')
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold tracking-tight">{data.filename}</h1>
          <p className="text-xs text-ink-500">
            {data.doc_type} · uploaded {formatDateTime(data.uploaded_at)} · {data.processing_ms} ms
          </p>
        </div>
        <ConfidenceTag score={data.overall_confidence} />
        <StatusBadge status={data.status} />
      </header>

      {banner && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-800">
          {banner} <Link to="/queue" className="font-medium underline">Back to queue</Link>
        </div>
      )}
      {actionError && <ErrorNotice error={actionError} />}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Panel title="Document" className="xl:sticky xl:top-6 xl:self-start">
          <div className="overflow-hidden rounded-xl border border-ink-200 bg-white">
            {isPdf && (
              <object data={api.fileUrl(data.id)} type="application/pdf" className="h-[70vh] w-full">
                <p className="p-4 text-sm text-ink-500">
                  Inline PDF preview unavailable.{' '}
                  <a className="underline" href={api.fileUrl(data.id)} target="_blank" rel="noreferrer">
                    Open the file
                  </a>
                  .
                </p>
              </object>
            )}
            {isImage && (
              <img src={api.fileUrl(data.id)} alt={data.filename} className="max-h-[70vh] w-full object-contain" />
            )}
            {!isPdf && !isImage && (
              <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap p-4 text-xs text-ink-700">
                {data.raw_text}
              </pre>
            )}
          </div>
          {focused && (
            <p className="mt-3 flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50/80 px-3 py-2 text-xs text-sky-800">
              <FileText className="h-3.5 w-3.5" />
              Isolating <span className="font-semibold">{focused}</span>
              {data.fields.find((f) => f.field_key === focused)?.bbox
                ? ` — source ${data.fields.find((f) => f.field_key === focused)?.bbox}`
                : ' — no positional anchor captured for this field'}
            </p>
          )}
        </Panel>

        <div className="space-y-5">
          {data.validation_issues.length > 0 && (
            <div className="space-y-2">
              {data.validation_issues.map((issue) => (
                <div
                  key={`${issue.rule}-${issue.message}`}
                  className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-sm ${
                    issue.severity === 'error'
                      ? 'border-rose-200 bg-rose-50/80 text-rose-800'
                      : 'border-amber-200 bg-amber-50/80 text-amber-800'
                  }`}
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-medium capitalize">{issue.rule.replace(/_/g, ' ')}</p>
                    <p className="mt-0.5">{issue.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Panel title="Extracted data">
            <div className="space-y-3">
              {data.fields.map((field) => {
                const failing = failingFields.has(field.field_key)
                return (
                  <div
                    key={field.id}
                    className={`rounded-xl border p-3 transition ${
                      focused === field.field_key
                        ? 'border-sky-300 bg-sky-50/60'
                        : failing
                          ? 'border-rose-200 bg-rose-50/40'
                          : 'border-ink-200 bg-white/50'
                    }`}
                  >
                    <div className="mb-1.5 flex items-center justify-between gap-2">
                      <label
                        htmlFor={`field-${field.id}`}
                        className="text-xs font-medium uppercase tracking-wide text-ink-500"
                      >
                        {field.field_key.replace(/_/g, ' ')}
                      </label>
                      <ConfidenceTag score={field.confidence_score} />
                    </div>
                    <input
                      id={`field-${field.id}`}
                      className="input-base"
                      value={values[field.field_key] ?? ''}
                      disabled={decided}
                      onFocus={() => setFocused(field.field_key)}
                      onChange={(event) =>
                        setValues((current) => ({ ...current, [field.field_key]: event.target.value }))
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
                <Save className="h-4 w-4" /> Save Edits &amp; Complete
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

          <Panel title="Audit trail">
            <ol className="space-y-2.5">
              {data.audit_logs.map((log) => (
                <li key={log.id} className="flex gap-3 text-xs">
                  <span className="w-28 shrink-0 text-ink-500">{formatDateTime(log.timestamp)}</span>
                  <span className="w-44 shrink-0 font-medium">{log.action}</span>
                  <span className="min-w-0 flex-1 truncate text-ink-700" title={log.details}>
                    {log.details}
                  </span>
                  <span className="shrink-0 text-ink-500">{log.performed_by}</span>
                </li>
              ))}
            </ol>
          </Panel>
        </div>
      </div>
    </div>
  )
}
