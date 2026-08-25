import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Clock, ShieldAlert, XCircle } from 'lucide-react'
import type { DocStatus } from '../lib/api'

export const STATUS_META: Record<DocStatus, { label: string; classes: string; Icon: typeof CheckCircle2 }> = {
  AUTO_APPROVED: {
    label: 'Approved',
    classes: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Icon: CheckCircle2,
  },
  APPROVED: {
    label: 'Approved (Human)',
    classes: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Icon: CheckCircle2,
  },
  NEEDS_REVIEW: {
    label: 'Review Required',
    classes: 'bg-amber-50 text-amber-700 border-amber-200',
    Icon: Clock,
  },
  ACTION_REQUIRED: {
    label: 'Action Required',
    classes: 'bg-rose-50 text-rose-700 border-rose-200',
    Icon: ShieldAlert,
  },
  REJECTED: { label: 'Rejected', classes: 'bg-rose-50 text-rose-700 border-rose-200', Icon: XCircle },
  FAILED: { label: 'Failed', classes: 'bg-rose-50 text-rose-700 border-rose-200', Icon: AlertTriangle },
  PROCESSING: { label: 'Processing', classes: 'bg-sky-50 text-sky-700 border-sky-200', Icon: Clock },
  UPLOADED: { label: 'Uploaded', classes: 'bg-slate-50 text-ink-700 border-ink-200', Icon: Clock },
}

export function StatusBadge({ status }: { status: DocStatus }) {
  const meta = STATUS_META[status]
  const Icon = meta.Icon
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${meta.classes}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {meta.label}
    </span>
  )
}

export function confidenceTone(score: number) {
  if (score >= 0.9) return { label: 'High', classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
  if (score >= 0.7) return { label: 'Medium', classes: 'bg-amber-50 text-amber-700 border-amber-200' }
  return { label: 'Low', classes: 'bg-rose-50 text-rose-700 border-rose-200' }
}

export function ConfidenceTag({ score }: { score: number }) {
  const tone = confidenceTone(score)
  return (
    <span className={`rounded-md border px-2 py-0.5 text-xs font-semibold tabular-nums ${tone.classes}`}>
      {(score * 100).toFixed(0)}%
    </span>
  )
}

export function Panel({
  title,
  action,
  children,
  className = '',
}: {
  title?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`glass p-5 ${className}`}>
      {(title || action) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="panel-title">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  )
}

export function EmptyState({ message }: { message: string }) {
  return <p className="py-8 text-center text-sm text-ink-500">{message}</p>
}

export function ErrorNotice({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-800">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">
        <p className="font-medium">Something went wrong</p>
        <p className="mt-0.5 text-rose-700">{error}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
