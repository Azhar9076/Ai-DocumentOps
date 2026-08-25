import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type DocStatus } from '../lib/api'
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
  const [filter, setFilter] = useState<DocStatus | 'ALL'>('ALL')
  const { data, error, loading, reload } = useAsync(
    () => api.documents(filter === 'ALL' ? undefined : filter),
    [filter],
  )

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Review Queue</h1>
        <p className="mt-1 text-sm text-ink-500">
          Documents routed by confidence and deterministic rule outcomes.
        </p>
      </header>

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
        <ul className="divide-y divide-ink-200/70">
          {(data ?? []).map((doc) => (
            <li key={doc.id}>
              <Link
                to={`/documents/${doc.id}`}
                className="flex flex-wrap items-center gap-3 px-1 py-3 transition hover:bg-white/60"
              >
                <span className="min-w-0 flex-1 truncate text-sm font-medium">{doc.filename}</span>
                <span className="rounded-md border border-ink-200 px-2 py-0.5 text-xs text-ink-700">
                  {doc.doc_type}
                </span>
                <ConfidenceTag score={doc.overall_confidence} />
                <StatusBadge status={doc.status} />
                <span className="w-32 text-right text-xs text-ink-500">
                  {formatDateTime(doc.uploaded_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
