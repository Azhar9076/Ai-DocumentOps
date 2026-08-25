import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, UploadCloud } from 'lucide-react'
import { api, type DocumentDetail } from '../lib/api'
import { ConfidenceTag, ErrorNotice, Panel, StatusBadge } from '../components/ui'

const STEPS = [
  'Uploaded',
  'OCR Processing',
  'Classified',
  'Field Extraction',
  'Validating Rules',
  'Complete',
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

  async function handleFile(file: File) {
    setError(null)
    setResult(null)
    setFileName(file.name)
    setStep(0)
    const ticker = window.setInterval(() => {
      setStep((current) => (current < STEPS.length - 2 ? current + 1 : current))
    }, 550)
    try {
      const detail = await api.upload(file)
      setResult(detail)
      setStep(STEPS.length - 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStep(-1)
    } finally {
      window.clearInterval(ticker)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Upload &amp; Process</h1>
        <p className="mt-1 text-sm text-ink-500">
          PDF, PNG, JPG and DOCX are parsed, classified, extracted and validated in one pass.
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
          className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-16 text-center transition ${
            dragging ? 'border-ink-900 bg-white/80' : 'border-ink-200 bg-white/40 hover:bg-white/70'
          }`}
        >
          <UploadCloud className="h-9 w-9 text-ink-500" />
          <p className="mt-4 text-base font-medium">Drop a document here</p>
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
        <Panel title={`Pipeline progress${fileName ? ` — ${fileName}` : ''}`}>
          <ol className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:grid-cols-6">
            {STEPS.map((label, index) => {
              const done = index < step || (result !== null && index <= step)
              const active = index === step && result === null
              return (
                <motion.li
                  key={label}
                  layout
                  className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 text-sm ${
                    done
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                      : active
                        ? 'border-sky-200 bg-sky-50 text-sky-800'
                        : 'border-ink-200 bg-white/50 text-ink-500'
                  }`}
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : active ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <span className="h-4 w-4 rounded-full border border-current opacity-40" />
                  )}
                  {label}
                </motion.li>
              )
            })}
          </ol>
        </Panel>
      )}

      {result && (
        <Panel title="Result">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={result.status} />
            <ConfidenceTag score={result.overall_confidence} />
            <span className="rounded-md border border-ink-200 px-2 py-0.5 text-xs text-ink-700">
              {result.doc_type}
            </span>
            <span className="text-xs text-ink-500">{result.processing_ms} ms</span>
            <button
              type="button"
              className="btn-primary ml-auto"
              onClick={() => navigate(`/documents/${result.id}`)}
            >
              Open verification view
            </button>
          </div>
          {result.validation_issues.length > 0 && (
            <ul className="mt-4 space-y-2">
              {result.validation_issues.map((issue) => (
                <li
                  key={`${issue.rule}-${issue.message}`}
                  className="rounded-xl border border-rose-200 bg-rose-50/80 px-3 py-2 text-sm text-rose-800"
                >
                  <span className="font-medium">{issue.rule}</span>: {issue.message}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}
    </div>
  )
}
