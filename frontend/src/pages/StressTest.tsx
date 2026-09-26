import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Gauge,
  Loader2,
  Sliders,
  Zap,
} from 'lucide-react'
import { api, type DocumentSummary, type RoutingThresholds } from '../lib/api'
import { useAuth } from '../lib/authContext'
import { useAsync } from '../lib/hooks'
import { ConfidenceTag, EmptyState, ErrorNotice, Panel, StatusBadge } from '../components/ui'

export function StressTest() {
  const { isAdmin } = useAuth()
  const [sampleCount, setSampleCount] = useState<number>(5)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeJobIds, setActiveJobIds] = useState<string[]>([])
  const [batchDocs, setBatchDocs] = useState<DocumentSummary[]>([])
  const [budgetRemaining, setBudgetRemaining] = useState<number | null>(null)
  const [maxBudget, setMaxBudget] = useState<number>(200)

  const thresholdsAsync = useAsync(() => api.getThresholds(), [])
  const [thresholds, setThresholds] = useState<RoutingThresholds>({
    auto_approved_min: 0.9,
    needs_review_min: 0.7,
  })
  const [savingThresholds, setSavingThresholds] = useState(false)
  const [thresholdSavedNotice, setThresholdSavedNotice] = useState<string | null>(null)

  useEffect(() => {
    if (thresholdsAsync.data) {
      setThresholds(thresholdsAsync.data)
    }
  }, [thresholdsAsync.data])

  useEffect(() => {
    if (activeJobIds.length === 0) return

    const interval = setInterval(async () => {
      try {
        const docs = await api.stressTestStatus(activeJobIds)
        setBatchDocs(docs)
        const allDone = docs.every((d) => d.status !== 'PROCESSING' && d.status !== 'UPLOADED')
        if (allDone && docs.length >= activeJobIds.length) {
          setRunning(false)
        }
      } catch (err) {
        console.error('Failed to poll stress-test status:', err)
      }
    }, 800)

    return () => clearInterval(interval)
  }, [activeJobIds])

  async function handleStartStressTest() {
    setRunning(true)
    setError(null)
    setBatchDocs([])
    setActiveJobIds([])

    try {
      const res = await api.stressTest(sampleCount)
      setActiveJobIds(res.job_ids)
      setBudgetRemaining(res.budget_remaining)
      setMaxBudget(res.max_calls)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setRunning(false)
    }
  }

  async function handleSaveThresholds(e: React.FormEvent) {
    e.preventDefault()
    setSavingThresholds(true)
    setThresholdSavedNotice(null)
    try {
      const updated = await api.updateThresholds(thresholds)
      setThresholds(updated)
      setThresholdSavedNotice('Routing thresholds updated live! Next batch will apply these cutoffs.')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSavingThresholds(false)
    }
  }

  const completedCount = batchDocs.filter(
    (d) => d.status !== 'PROCESSING' && d.status !== 'UPLOADED',
  ).length

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Intake Stress-Tester &amp; Threshold Studio</h1>
          <p className="mt-1 text-sm text-ink-500">
            Simulate concurrent high-volume document intake to demonstrate connection-pool resilience, Granite budget guards, and dynamic routing cutoffs.
          </p>
        </div>

        {budgetRemaining !== null && (
          <div className="flex items-center gap-2 rounded-xl border border-sky-200 bg-sky-50/80 px-3.5 py-2 text-xs text-sky-900">
            <Gauge className="h-4 w-4 text-sky-600" />
            <span>
              Granite Budget Guard: <strong className="font-mono">{budgetRemaining}/{maxBudget}</strong> calls remaining
            </span>
          </div>
        )}
      </header>

      {error && <ErrorNotice error={error} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel title="Concurrent Intake Simulator" className="lg:col-span-2">
          <div className="space-y-5">
            <p className="text-xs text-ink-600 leading-relaxed">
              Generate and stream synthetic invoices, contracts, and medical intake forms concurrently. Each document executes through the full 3-agent pipeline across scoped database sessions.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-ink-500 mb-1.5">
                  Sample Batch Size
                </label>
                <div className="flex items-center gap-2">
                  {[3, 5, 8, 10].map((count) => (
                    <button
                      key={count}
                      type="button"
                      disabled={running}
                      onClick={() => setSampleCount(count)}
                      className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                        sampleCount === count
                          ? 'bg-ink-900 text-white shadow-sm'
                          : 'border border-ink-200 bg-white/70 text-ink-700 hover:bg-white'
                      }`}
                    >
                      {count} Docs
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex-1 pt-5">
                <button
                  type="button"
                  disabled={running}
                  onClick={handleStartStressTest}
                  className="btn-primary w-full justify-center py-2.5 shadow-sm text-sm"
                >
                  {running ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing Batch ({completedCount}/{activeJobIds.length || sampleCount})...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 text-amber-300" />
                      Simulate High-Volume Intake ({sampleCount} Docs)
                    </>
                  )}
                </button>
              </div>
            </div>

            {activeJobIds.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-ink-600">
                  <span>
                    Concurrent Ingestion: <strong>{completedCount}</strong> of <strong>{activeJobIds.length}</strong> finished
                  </span>
                  <span className="font-mono font-bold text-ink-900">
                    {Math.round((completedCount / activeJobIds.length) * 100)}%
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-ink-100">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${(completedCount / activeJobIds.length) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </Panel>

        <Panel title="Dynamic Routing Cutoffs">
          <form onSubmit={handleSaveThresholds} className="space-y-4">
            <p className="text-xs text-ink-600">
              Adjust confidence cutoffs live to test straight-through automation rate trade-offs.
            </p>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="font-medium text-ink-700">Auto-Approve Min</label>
                <span className="font-mono font-semibold text-emerald-700">
                  {(thresholds.auto_approved_min * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.75"
                max="0.98"
                step="0.01"
                value={thresholds.auto_approved_min}
                onChange={(e) =>
                  setThresholds((prev) => ({
                    ...prev,
                    auto_approved_min: parseFloat(e.target.value),
                  }))
                }
                className="w-full accent-emerald-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="font-medium text-ink-700">Review Required Min</label>
                <span className="font-mono font-semibold text-amber-700">
                  {(thresholds.needs_review_min * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.80"
                step="0.01"
                value={thresholds.needs_review_min}
                onChange={(e) =>
                  setThresholds((prev) => ({
                    ...prev,
                    needs_review_min: parseFloat(e.target.value),
                  }))
                }
                className="w-full accent-amber-600"
              />
            </div>

            <button
              type="submit"
              disabled={savingThresholds || !isAdmin}
              className="btn-secondary w-full justify-center text-xs"
            >
              <Sliders className="h-3.5 w-3.5" />
              {savingThresholds ? 'Saving...' : 'Apply Cutoffs Live'}
            </button>

            {thresholdSavedNotice && (
              <p className="text-[11px] text-emerald-700 bg-emerald-50 p-2 rounded-lg border border-emerald-200">
                {thresholdSavedNotice}
              </p>
            )}
          </form>
        </Panel>
      </div>

      <Panel title="Live Batch Stream Output">
        {batchDocs.length === 0 ? (
          <EmptyState message="Click 'Simulate High-Volume Intake' above to launch concurrent document processing." />
        ) : (
          <div className="divide-y divide-ink-200/70 overflow-hidden">
            {batchDocs.map((doc, idx) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.05 }}
                className="flex flex-wrap items-center gap-3 py-3 px-1 transition hover:bg-white/60"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink-100 text-xs font-bold text-ink-700 font-mono shrink-0">
                  #{idx + 1}
                </div>

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

                <span className="w-24 text-right text-xs text-ink-500 font-mono text-[11px]">
                  {doc.processing_ms > 0 ? `${doc.processing_ms} ms` : 'streaming...'}
                </span>

                <Link
                  to={`/documents/${doc.id}`}
                  className="btn-secondary text-xs py-1 px-2.5"
                  title="Open document verification view"
                >
                  Inspect <ArrowRight className="h-3 w-3 ml-1" />
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
