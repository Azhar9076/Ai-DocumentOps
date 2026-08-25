import { motion } from 'framer-motion'
import {
  Database,
  FileSearch,
  ScrollText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  UserCheck,
} from 'lucide-react'
import { Panel } from '../components/ui'

const STAGES = [
  {
    id: '01',
    title: 'Upload',
    Icon: UploadCloud,
    body: 'Files are validated by type and size, then written to durable storage with an immutable document id.',
  },
  {
    id: '02',
    title: 'Understand',
    Icon: FileSearch,
    body: 'PDF text layers are parsed; scans and images fall back to OCR, which also yields a page quality score.',
  },
  {
    id: '03',
    title: 'Extract',
    Icon: Sparkles,
    body: 'The classifier selects a strict Pydantic schema and every target field is extracted with its own 0.00–1.00 confidence.',
  },
  {
    id: '04',
    title: 'Validate',
    Icon: ShieldCheck,
    body: 'Deterministic rules run — subtotal + tax = total, date and email formats, required fields — penalising confidence on failure.',
  },
  {
    id: '05',
    title: 'Review',
    Icon: UserCheck,
    body: '≥90% auto-approves, 70–89% queues for human review, and anything below or with a rule failure demands verification.',
  },
  {
    id: '06',
    title: 'Store',
    Icon: Database,
    body: 'Documents, fields, corrections and confidence land in PostgreSQL as normalised, queryable records.',
  },
  {
    id: '07',
    title: 'Audit',
    Icon: ScrollText,
    body: 'Every state transition, score and reviewer edit is appended to an immutable audit trail with timestamps.',
  },
]

export function Workflow() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">How the automation engine works</h1>
        <p className="mt-1 text-sm text-ink-500">
          Seven deterministic stages between an unstructured file and trusted structured data.
        </p>
      </header>

      <Panel>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {STAGES.map((stage, index) => (
            <motion.article
              key={stage.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: index * 0.05 }}
              className="relative rounded-2xl border border-white/70 bg-white/60 p-5 backdrop-blur-md"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold tracking-[0.2em] text-ink-500">{stage.id}</span>
                <stage.Icon className="h-4 w-4 text-ink-700" />
              </div>
              <h3 className="mt-3 text-base font-semibold">{stage.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-700">{stage.body}</p>
            </motion.article>
          ))}
        </div>
      </Panel>

      <Panel title="Routing thresholds">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
            <p className="text-sm font-semibold text-emerald-800">Confidence ≥ 90%</p>
            <p className="mt-1 text-sm text-emerald-700">
              AUTO_APPROVED — written straight to the database with no human touch.
            </p>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4">
            <p className="text-sm font-semibold text-amber-800">Confidence 70–89%</p>
            <p className="mt-1 text-sm text-amber-700">
              NEEDS_REVIEW — queued for a reviewer to confirm the weakest fields.
            </p>
          </div>
          <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-4">
            <p className="text-sm font-semibold text-rose-800">Below 70% or rule failure</p>
            <p className="mt-1 text-sm text-rose-700">
              ACTION_REQUIRED — failing fields are highlighted for mandatory verification.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  )
}
