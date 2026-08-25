import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, Clock4, FileCheck2, Percent, Timer } from 'lucide-react'
import { api } from '../lib/api'
import { formatDateTime, useAsync } from '../lib/hooks'
import { ConfidenceTag, EmptyState, ErrorNotice, Panel, StatusBadge } from '../components/ui'

const CARD_ICONS = [FileCheck2, Percent, Clock4, Activity, Timer]

export function Dashboard() {
  const metrics = useAsync(() => api.metrics(), [])
  const documents = useAsync(() => api.documents(), [])

  if (metrics.error) return <ErrorNotice error={metrics.error} onRetry={metrics.reload} />

  const cards = metrics.data
    ? [
        { label: 'Documents Processed', value: metrics.data.documents_processed.toString() },
        { label: 'Auto-Automated', value: `${metrics.data.auto_automation_rate}%` },
        { label: 'Human Reviews Pending', value: metrics.data.reviews_pending.toString() },
        { label: 'Average Confidence', value: `${metrics.data.average_confidence}%` },
        { label: 'Est. Hours Saved', value: `${metrics.data.estimated_hours_saved}` },
      ]
    : []

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Dashboard</h1>
          <p className="mt-1 text-sm text-ink-500">
            Straight-through processing performance across every ingested document.
          </p>
        </div>
        <Link to="/upload" className="btn-primary">
          Process a document
        </Link>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map((card, index) => {
          const Icon = CARD_ICONS[index]
          return (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: index * 0.04 }}
              className="glass p-5"
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium uppercase tracking-wide text-ink-500">
                  {card.label}
                </p>
                <Icon className="h-4 w-4 text-ink-500" />
              </div>
              <p className="mt-3 text-3xl font-semibold tabular-nums">{card.value}</p>
            </motion.div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Panel title="Accuracy trend (7 days)">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics.data?.accuracy_trend ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(value) => `${Number(value)}%`} />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="#0f172a"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Confidence distribution">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.data?.confidence_distribution ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#334155" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel
        title="Recent queue"
        action={
          <Link to="/queue" className="text-sm font-medium text-ink-700 hover:underline">
            View all
          </Link>
        }
      >
        {documents.error && <ErrorNotice error={documents.error} onRetry={documents.reload} />}
        {!documents.error && (documents.data?.length ?? 0) === 0 && !documents.loading && (
          <EmptyState message="No documents processed yet. Upload one to get started." />
        )}
        <ul className="divide-y divide-ink-200/70">
          {(documents.data ?? []).slice(0, 8).map((doc) => (
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
