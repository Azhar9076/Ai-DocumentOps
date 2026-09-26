import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, Sparkles, StopCircle, UploadCloud } from 'lucide-react'
import { api, type DocumentDetail } from '../lib/api'
import { ConfidenceTag, ErrorNotice, Panel, StatusBadge } from '../components/ui'

const AGENT_STEPS = [
  { id: 'docling', label: 'IBM Docling Layout Parsing', sub: 'Markdown structure & coordinates' },
  { id: 'classifier', label: 'Stage 1: Granite Classifier', sub: 'Doc type & routing schema branch' },
  { id: 'extractor', label: 'Stage 2: Schema Extractor', sub: 'Prompt v2 few-shot field vectors' },
  { id: 'validator', label: 'Stage 3: Validation & Self-Correction', sub: 'Deterministic arithmetic & rule audit' },
  { id: 'auditor', label: 'Stage 4: AI Compliance Auditor', sub: 'Granite natural-language audit summary' },
  { id: 'complete', label: 'Pipeline Complete', sub: 'Persisted to audit lineage' },
]

const ACCEPT = '.pdf,.png,.jpg,.jpeg,.docx'

export function Upload() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [step, setStep] = useState(-1)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DocumentDetail | null>(null)
  const [fileName, setFileName] = useState('')
  const [inProgressId, setInProgressId] = useState<string | null>(null)
  const [cancelled, setCancelled] = useState(false)

  async function handleFile(file: File) {
    setError(null)
    setResult(null)
    setCancelled(false)
    setFileName(file.name)
    setStep(0)

    const ticker = window.setInterval(() => {
      setStep((current) => (current < AGENT_STEPS.length - 2 ? current + 1 : current))
    }, 450)

    try {
      const detail = await api.upload(file)
      setInProgressId(detail.id)
      setResult(detail)
      setStep(AGENT_STEPS.length - 1)
    } catch (err) {
      if (!cancelled) {
        setError(err instanceof Error ? err.message : String(err))
        setStep(-1)
      }
    } finally {
      window.clearInterval(ticker)
    }
  }

  async function handleCancel() {
    if (inProgressId) {
      try {
        await api.cancel(inProgressId)
        setCancelled(true)
        setError('Pipeline execution cancelled by user.')
        setStep(-1)
      } catch (err) {
        console.error('Cancel failed', err)
      }
    } else {
      setCancelled(true)
      setStep(-1)
      setError('Upload cancelled.')
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Upload &amp; Process</h1>
        <p className="mt-1 text-sm text-ink-500">
          Layout-aware parsing with IBM Docling followed by a 3-agent Granite 3.0 extraction and compliance audit pipeline.
        </p>
      </header>

      {error && <ErrorNotice error={error} />}

      <Panel>
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click()
          }}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragging(false)
            const file = event.dataTransfer.files?.[0]
            if (file) void handleFile(file)
          }}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition ${
            dragging ? 'border-ink-900 bg-white/80' : 'border-ink-200 bg-white/40 hover:bg-white/70'
          }`}
        >
          <UploadCloud className="h-10 w-10 text-ink-500" />
          <p className="mt-4 text-base font-medium">Drop an invoice, contract, or form here</p>
          <p className="mt-1 text-sm text-ink-500">or click to browse — PDF, PNG, JPG, DOCX (max 25MB)</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void handleFile(file)
              event.target.value = ''
            }}
          />
        </div>
      </Panel>

      {step >= 0 && (
        <Panel
          title={`Sequential Agent Pipeline Execution${fileName ? ` — ${fileName}` : ''}`}
          action={
            step < AGENT_STEPS.length - 1 && (
              <button
                type="button"
                onClick={handleCancel}
                className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 transition"
              >
                <StopCircle className="h-3.5 w-3.5" /> Cancel Execution
              </button>
            )
          }
        >
          <ol className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {AGENT_STEPS.map((item, index) => {
              const done = index < step || (result !== null && index <= step)
              const active = index === step && result === null
              return (
                <motion.li
                  key={item.id}
                  layout
                  className={`flex items-start gap-3 rounded-xl border p-3 text-sm transition ${
                    done
                      ? 'border-emerald-200 bg-emerald-50/90 text-emerald-900'
                      : active
                        ? 'border-sky-300 bg-sky-50 text-sky-900 shadow-sm'
                        : 'border-ink-200 bg-white/40 text-ink-400'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {done ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    ) : active ? (
                      <Loader2 className="h-4 w-4 animate-spin text-sky-600" />
                    ) : (
                      <span className="inline-block h-4 w-4 rounded-full border border-current opacity-30" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium leading-tight">{item.label}</p>
                    <p className="mt-0.5 text-xs opacity-75">{item.sub}</p>
                  </div>
                </motion.li>
              )
            })}
          </ol>
        </Panel>
      )}

      {result && (
        <Panel title="Pipeline Outcome &amp; Audit Trace">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge status={result.status} />
              <ConfidenceTag score={result.overall_confidence} />
              <span className="rounded-md border border-ink-200 bg-white px-2 py-0.5 text-xs font-medium text-ink-700">
                {result.doc_type}
              </span>
              <span className="text-xs text-ink-500 tabular-nums">Latency: {result.processing_ms} ms</span>
              <button
                type="button"
                className="btn-primary ml-auto"
                onClick={() => navigate(`/documents/${result.id}`)}
              >
                Open Verification &amp; Explainability View
              </button>
            </div>

            {/* Section 2: AI Audit Summary Badge */}
            {result.audit_summary && (
              <div className="flex items-start gap-2.5 rounded-xl border border-sky-200 bg-sky-50/90 p-4 text-xs leading-relaxed text-sky-950">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-sky-600" />
                <div>
                  <span className="font-semibold uppercase tracking-wide text-sky-800">
                    Granite Compliance Summary:
                  </span>{' '}
                  {result.audit_summary}
                </div>
              </div>
            )}

            {result.validation_issues.length > 0 && (
              <ul className="space-y-2">
                {result.validation_issues.map((issue) => (
                  <li
                    key={`${issue.rule}-${issue.message}`}
                    className="rounded-xl border border-rose-200 bg-rose-50/80 px-3.5 py-2.5 text-xs text-rose-800"
                  >
                    <span className="font-semibold capitalize">{issue.rule.replace(/_/g, ' ')}</span>: {issue.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Panel>
      )}
    </div>
  )
}
