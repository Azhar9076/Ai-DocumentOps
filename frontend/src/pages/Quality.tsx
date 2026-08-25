import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Info } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { EmptyState, ErrorNotice, Panel } from '../components/ui'

export function Quality() {
  const { data, error, loading, reload } = useAsync(() => api.quality(), [])

  if (error) return <ErrorNotice error={error} onRetry={reload} />

  const cards = data
    ? [
        { label: 'Overall Accuracy', value: `${data.overall_accuracy}%` },
        { label: 'Math Validation Pass Rate', value: `${data.math_validation_pass_rate}%` },
        { label: 'Human Correction Rate', value: `${data.human_correction_rate}%` },
        { label: 'Documents Evaluated', value: `${data.sample_size}` },
      ]
    : []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Accuracy &amp; Quality</h1>
        <p className="mt-1 text-sm text-ink-500">
          Extraction quality measured across the evaluated document set.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="glass p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{card.label}</p>
            <p className="mt-3 text-3xl font-semibold tabular-nums">{card.value}</p>
          </div>
        ))}
      </div>

      <Panel title="Field-level accuracy">
        {!loading && (data?.field_accuracy.length ?? 0) === 0 && (
          <EmptyState message="No extracted fields have been evaluated yet." />
        )}
        {(data?.field_accuracy.length ?? 0) > 0 && (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.field_accuracy ?? []} margin={{ bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis
                  dataKey="field_key"
                  tick={{ fontSize: 11 }}
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => `${Number(value)}%`} />
                <Bar dataKey="accuracy" fill="#334155" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>

      <div className="flex items-start gap-2.5 rounded-xl border border-ink-200 bg-white/60 p-4 text-sm text-ink-700 backdrop-blur-md">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-ink-500" />
        <p>{data?.notice ?? 'Metrics evaluated against project standard ground-truth test suite.'}</p>
      </div>
    </div>
  )
}
