import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, CheckSquare, Sparkles, Square, X } from 'lucide-react'
import { api, type DocStatus } from '../lib/api'
import { useAuth } from '../lib/authContext'
import { formatDateTime, useAsync } from '../lib/hooks'
import { ConfidenceTag, EmptyState, ErrorNotice, Panel, StatusBadge } from '../components/ui'

const FILTERS: { label: string; value: DocStatus | 'ALL' }[] = [
  { label: 'All', value: 'ALL' },
  { label: 'Approved', value: 'AUTO_APPROVED' },
  { label: 'Review Required', value: 'NEEDS_REVIEW' },
  { label: 'Action Required', value: 'ACTION_REQUIRED' },
  { label: 'Rejected', value: 'REJECTED' },
]

export function Queue() {
  const { userEmail } = useAuth()
  const [filter, setFilter] = useState<DocStatus | 'ALL'>('ALL')
  const { data, error, loading, reload } = useAsync(
    () => api.documents(filter === 'ALL' ? undefined : filter),
    [filter],
  )
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkActing, setBulkActing] = useState(false)
  const [bulkNotice, setBulkNotice] = useState<string | null>(null)

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function selectAll() {
    if (!data) return
    if (selectedIds.size === data.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(data.map((d) => d.id)))
    }
  }

  async function handleBulkAction(decision: 'APPROVE' | 'REJECT') {
    if (selectedIds.size === 0) return
    setBulkActing(true)
    setBulkNotice(null)
    try {
      await api.bulkReview({
        document_ids: Array.from(selectedIds),
        decision,
        reviewer_id: userEmail,
      })
      setBulkNotice(`Bulk ${decision.toLowerCase()} applied to ${selectedIds.size} document(s).`)
      setSelectedIds(new Set())
      reload()
    } catch (err) {
      setBulkNotice(err instanceof Error ? err.message : String(err))
    } finally {
      setBulkActing(false)
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Review Queue</h1>
          <p className="mt-1 text-sm text-ink-500">
            Documents routed by IBM Granite 3.0 confidence scoring and deterministic rule validation.
          </p>
        </div>

        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 rounded-xl border border-ink-200 bg-white p-1.5 shadow-sm">
            <span className="px-2 text-xs font-semibold text-ink-700">
              {selectedIds.size} selected
            </span>
            <button
              type="button"
              className="btn-primary text-xs py-1"
              disabled={bulkActing}
              onClick={() => handleBulkAction('APPROVE')}
            >
              <Check className="h-3.5 w-3.5" /> Approve
            </button>
            <button
              type="button"
              className="btn-danger text-xs py-1"
              disabled={bulkActing}
              onClick={() => handleBulkAction('REJECT')}
            >
              <X className="h-3.5 w-3.5" /> Reject
            </button>
          </div>
        )}
      </header>

      {bulkNotice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/90 p-3 text-xs font-medium text-emerald-900">
          {bulkNotice}
        </div>
      )}

      <Panel
        action={
          <div className="flex flex-wrap gap-2">
            {FILTERS.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setFilter(item.value)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                  filter === item.value
                    ? 'border-ink-900 bg-ink-900 text-white'
                    : 'border-ink-200 bg-white/70 text-ink-700 hover:bg-white'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        }
      >
        {error && <ErrorNotice error={error} onRetry={reload} />}
        {!error && !loading && (data?.length ?? 0) === 0 && (
          <EmptyState message="No documents match this filter." />
        )}

        {(data?.length ?? 0) > 0 && (
          <div className="mb-2 flex items-center justify-between border-b border-ink-200/60 pb-2 text-xs text-ink-500">
            <button
              type="button"
              onClick={selectAll}
              className="inline-flex items-center gap-1.5 font-medium hover:text-ink-900"
            >
              {selectedIds.size === data?.length ? (
                <CheckSquare className="h-4 w-4 text-ink-900" />
              ) : (
                <Square className="h-4 w-4" />
              )}
              Select All ({data?.length})
            </button>
          </div>
        )}

        <ul className="divide-y divide-ink-200/70">
          {(data ?? []).map((doc) => {
            const isSelected = selectedIds.has(doc.id)
            return (
              <li
                key={doc.id}
                className={`flex flex-wrap items-center gap-3 px-2 py-3 transition ${
                  isSelected ? 'bg-sky-50/70' : 'hover:bg-white/60'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSelect(doc.id)}
                  className="h-4 w-4 rounded border-ink-300 text-ink-900 focus:ring-ink-900"
                />

                <Link to={`/documents/${doc.id}`} className="min-w-0 flex-1 flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-ink-900">{doc.filename}</span>
                    <span className="rounded-md border border-ink-200 px-2 py-0.2 text-[11px] text-ink-700">
                      {doc.doc_type}
                    </span>
                  </div>
                  {doc.audit_summary && (
                    <p className="mt-0.5 truncate text-[11px] text-ink-500 flex items-center gap-1">
                      <Sparkles className="h-3 w-3 text-sky-600 shrink-0" />
                      {doc.audit_summary}
                    </p>
                  )}
                </Link>

                <ConfidenceTag score={doc.overall_confidence} />
                <StatusBadge status={doc.status} />
                <span className="w-28 text-right text-xs text-ink-400 font-mono text-[11px]">
                  {formatDateTime(doc.uploaded_at)}
                </span>
              </li>
            )
          })}
        </ul>
      </Panel>
    </div>
  )
}
