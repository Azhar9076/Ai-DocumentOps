import { useState } from 'react'
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
import {
  BarChart3,
  Clock4,
  FileCheck2,
  FileStack,
  Percent,
  ShieldCheck,
  Sparkles,
  Timer,
} from 'lucide-react'
import { GovernanceTrustTab } from '../components/GovernanceTrustTab'
import { api } from '../lib/api'
import { formatDateTime, useAsync } from '../lib/hooks'
import { ConfidenceTag, EmptyState, ErrorNotice, Panel, StatusBadge } from '../components/ui'
import { Quality } from './Quality'

const CARD_ICONS = [FileCheck2, Percent, Clock4, ShieldCheck, Timer]

export function Dashboard() {
  const [activeMainTab, setActiveMainTab] = useState<'pipeline' | 'accuracy' | 'governance'>('pipeline')
  const metrics = useAsync(() => api.metrics(), [])
  const documents = useAsync(() => api.documents(), [])

  if (metrics.error) return <ErrorNotice error={metrics.error} onRetry={metrics.reload} />

  const cards = metrics.data
    ? [
        { label: 'Documents Processed', value: metrics.data.documents_processed.toString() },
        { label: 'Straight-Through Rate', value: `${metrics.data.auto_automation_rate}%` },
        { label: 'Human Reviews Pending', value: metrics.data.reviews_pending.toString() },
        { label: 'Average Confidence', value: `${metrics.data.average_confidence}%` },
        { label: 'Est. Hours Saved', value: `${metrics.data.estimated_hours_saved}h` },
      ]
    : []

  const roi = metrics.data?.roi_metrics

  return (
    <div className="space-y-6">
      {/* 3 Main Executive Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-ink-200/80 bg-white/70 p-1.5 backdrop-blur-md shadow-sm">
        <button
          type="button"
          onClick={() => setActiveMainTab('pipeline')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
            activeMainTab === 'pipeline'
              ? 'bg-ink-900 text-white shadow-sm'
              : 'text-ink-600 hover:bg-white hover:text-ink-900'
          }`}
        >
          <FileStack className="h-3.5 w-3.5" />
          Pipeline &amp; Review
        </button>

        <button
          type="button"
          onClick={() => setActiveMainTab('accuracy')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
            activeMainTab === 'accuracy'
              ? 'bg-ink-900 text-white shadow-sm'
              : 'text-ink-600 hover:bg-white hover:text-ink-900'
          }`}
        >
          <BarChart3 className="h-3.5 w-3.5" />
          Accuracy &amp; ROI Dashboard
        </button>

        <button
          type="button"
          onClick={() => setActiveMainTab('governance')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
            activeMainTab === 'governance'
              ? 'bg-slate-950 text-emerald-400 border border-emerald-500/40 shadow-sm'
              : 'text-ink-600 hover:bg-white hover:text-ink-900'
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          IBM Governance &amp; Trust
        </button>
      </div>

      {activeMainTab === 'governance' && <GovernanceTrustTab />}
      {activeMainTab === 'accuracy' && <Quality />}

      {activeMainTab === 'pipeline' && (
        <>
          <header className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">Executive Dashboard</h1>
              <p className="mt-1 text-sm text-ink-500">
                Straight-through processing and compliance audit performance across all ingested documents.
              </p>
            </div>
            <Link to="/upload" className="btn-primary">
              Process a document
            </Link>
          </header>

          {/* KPI Cards */}
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
                    <p className="text-xs font-semibold uppercase tracking-wider text-ink-500">
                      {card.label}
                    </p>
                    <Icon className="h-4 w-4 text-ink-400" />
                  </div>
                  <p className="mt-3 text-3xl font-bold tabular-nums text-ink-900">{card.value}</p>
                </motion.div>
              )
            })}
          </div>

          {/* ROI Impact Highlight */}
          {roi && (
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-emerald-200 bg-emerald-50/80 p-5 text-emerald-950 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-emerald-100 p-2.5 text-emerald-800">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                    Business Impact &amp; ROI Metric
                  </p>
                  <p className="text-base font-semibold">
                    Estimated <span className="underline decoration-emerald-500">{roi.hours_saved_per_100_docs ?? 12.5} hours</span> manual review time saved per 100 documents with {roi.cost_reduction_est ?? '74%'} operational cost reduction.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveMainTab('accuracy')}
                className="btn-secondary text-xs bg-white text-emerald-900 border-emerald-300 hover:bg-emerald-100/50"
              >
                View Benchmark Rigor
              </button>
            </div>
          )}

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
                      strokeWidth={2.5}
                      dot={{ r: 3.5 }}
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
            title="Recent Ingestion Queue"
            action={
              <Link to="/queue" className="text-xs font-semibold text-ink-700 hover:underline">
                View all documents
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
                    <div className="min-w-0 flex-1 flex flex-col">
                      <span className="truncate text-sm font-medium text-ink-900">{doc.filename}</span>
                      {doc.audit_summary && (
                        <span className="truncate text-[11px] text-ink-500">{doc.audit_summary}</span>
                      )}
                    </div>
                    <span className="rounded-md border border-ink-200 px-2 py-0.5 text-xs text-ink-700">
                      {doc.doc_type}
                    </span>
                    <ConfidenceTag score={doc.overall_confidence} />
                    <StatusBadge status={doc.status} />
                    <span className="w-28 text-right text-xs text-ink-400 font-mono text-[11px]">
                      {formatDateTime(doc.uploaded_at)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>
        </>
      )}
    </div>
  )
}
