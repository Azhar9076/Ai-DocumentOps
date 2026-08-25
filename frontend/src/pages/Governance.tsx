import { motion } from 'framer-motion'
import { Shield, Cpu, FileText, Activity, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { Panel, EmptyState, ErrorNotice } from '../components/ui'

interface IBMStackInfo {
  docling: { installed: boolean; version: string; status: string }
  watsonx_ai: { installed: boolean; version: string; status: string }
  granite_model: { model_id: string; provider: string; deployment: string }
  overall_status: string
}

interface GovernanceReport {
  report_generated_at: string
  model_stack: { document_parser: string; llm_provider: string; llm_model: string; llm_status: string }
  processing_statistics: {
    total_documents: number
    status_breakdown: Record<string, number>
    average_confidence: number
    total_processing_time_ms: number
    average_processing_time_ms: number
  }
  audit_statistics: { total_audit_entries: number; compliance_rate: number }
  system_health: { ibm_integration_active: boolean; fallback_mode_active: boolean }
}

export function Governance() {
  const stackInfo = useAsync<IBMStackInfo>(() => api.getIBMStackInfo(), [])
  const governanceReport = useAsync<GovernanceReport>(() => api.getGovernanceReport(), [])

  if (stackInfo.error) return <ErrorNotice error={stackInfo.error} onRetry={stackInfo.reload} />
  if (governanceReport.error) return <ErrorNotice error={governanceReport.error} onRetry={governanceReport.reload} />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">IBM Governance & Trust</h1>
        <p className="mt-1 text-sm text-ink-500">
          Monitor IBM stack health, compliance, and document processing lineage.
        </p>
      </header>

      {/* IBM Stack Status */}
      <Panel title="IBM Stack Status">
        {stackInfo.loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-ink-300 border-t-ink-900"></div>
          </div>
        ) : stackInfo.data ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${stackInfo.data.overall_status === 'operational' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                <span className="font-medium">Overall Status</span>
              </div>
              <span className={`text-sm font-medium ${stackInfo.data.overall_status === 'operational' ? 'text-emerald-700' : 'text-amber-700'}`}>
                {stackInfo.data.overall_status === 'operational' ? 'Operational' : 'Degraded'}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg border border-ink-200 bg-white/50 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <h3 className="font-medium">IBM Docling</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-500">Status</span>
                    <span className={`font-medium ${stackInfo.data.docling.status === 'active' ? 'text-emerald-700' : 'text-amber-700'}`}>
                      {stackInfo.data.docling.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500">Version</span>
                    <span className="font-medium">{stackInfo.data.docling.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500">Installed</span>
                    <span className={`font-medium ${stackInfo.data.docling.installed ? 'text-emerald-700' : 'text-rose-700'}`}>
                      {stackInfo.data.docling.installed ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-lg border border-ink-200 bg-white/50 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Cpu className="h-5 w-5 text-purple-600" />
                  <h3 className="font-medium">IBM Watsonx.ai</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-500">Status</span>
                    <span className={`font-medium ${stackInfo.data.watsonx_ai.status === 'active' ? 'text-emerald-700' : 'text-amber-700'}`}>
                      {stackInfo.data.watsonx_ai.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500">Version</span>
                    <span className="font-medium">{stackInfo.data.watsonx_ai.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500">Installed</span>
                    <span className={`font-medium ${stackInfo.data.watsonx_ai.installed ? 'text-emerald-700' : 'text-rose-700'}`}>
                      {stackInfo.data.watsonx_ai.installed ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-lg border border-ink-200 bg-white/50 p-4 md:col-span-2"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="h-5 w-5 text-indigo-600" />
                  <h3 className="font-medium">IBM Granite 3.0 Model</h3>
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3 text-sm">
                  <div>
                    <span className="text-ink-500 block">Model ID</span>
                    <span className="font-medium">{stackInfo.data.granite_model.model_id}</span>
                  </div>
                  <div>
                    <span className="text-ink-500 block">Provider</span>
                    <span className="font-medium">{stackInfo.data.granite_model.provider}</span>
                  </div>
                  <div>
                    <span className="text-ink-500 block">Deployment</span>
                    <span className="font-medium">{stackInfo.data.granite_model.deployment}</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        ) : (
          <EmptyState message="Unable to load IBM stack information." />
        )}
      </Panel>

      {/* Governance Report */}
      <Panel title="System Governance Report">
        {governanceReport.loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-ink-300 border-t-ink-900"></div>
          </div>
        ) : governanceReport.data ? (
          <div className="space-y-6">
            {/* System Health */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg border border-ink-200 bg-white/50 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="h-5 w-5 text-emerald-600" />
                  <h3 className="font-medium">System Health</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-ink-500">IBM Integration</span>
                    {governanceReport.data.system_health.ibm_integration_active ? (
                      <CheckCircle className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-ink-500">Fallback Mode</span>
                    {governanceReport.data.system_health.fallback_mode_active ? (
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                    ) : (
                      <CheckCircle className="h-4 w-4 text-emerald-600" />
                    )}
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-lg border border-ink-200 bg-white/50 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="h-5 w-5 text-blue-600" />
                  <h3 className="font-medium">Compliance Rate</h3>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-3xl font-semibold">
                    {governanceReport.data.audit_statistics.compliance_rate}%
                  </div>
                  <div className="text-sm text-ink-500">
                    of documents passed validation
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Processing Statistics */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-lg border border-ink-200 bg-white/50 p-4"
            >
              <div className="flex items-center gap-2 mb-4">
                <Clock className="h-5 w-5 text-purple-600" />
                <h3 className="font-medium">Processing Statistics</h3>
              </div>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 text-sm">
                <div>
                  <span className="text-ink-500 block">Total Documents</span>
                  <span className="text-xl font-semibold">{governanceReport.data.processing_statistics.total_documents}</span>
                </div>
                <div>
                  <span className="text-ink-500 block">Average Confidence</span>
                  <span className="text-xl font-semibold">{(governanceReport.data.processing_statistics.average_confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-ink-500 block">Avg Processing Time</span>
                  <span className="text-xl font-semibold">{governanceReport.data.processing_statistics.average_processing_time_ms}ms</span>
                </div>
                <div>
                  <span className="text-ink-500 block">Total Audit Entries</span>
                  <span className="text-xl font-semibold">{governanceReport.data.audit_statistics.total_audit_entries}</span>
                </div>
              </div>

              {/* Status Breakdown */}
              <div className="mt-4 pt-4 border-t border-ink-200">
                <span className="text-ink-500 text-sm block mb-2">Status Breakdown</span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(governanceReport.data.processing_statistics.status_breakdown).map(([status, count]) => (
                    <div key={status} className="rounded-full bg-ink-100 px-3 py-1 text-sm">
                      <span className="font-medium">{status}</span>: {count}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Model Stack Information */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="rounded-lg border border-ink-200 bg-white/50 p-4"
            >
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="h-5 w-5 text-indigo-600" />
                <h3 className="font-medium">Active Model Stack</h3>
              </div>
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-ink-500">Document Parser</span>
                  <span className="font-medium">{governanceReport.data.model_stack.document_parser}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-500">LLM Provider</span>
                  <span className="font-medium">{governanceReport.data.model_stack.llm_provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-500">LLM Model</span>
                  <span className="font-medium">{governanceReport.data.model_stack.llm_model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-500">LLM Status</span>
                  <span className={`font-medium ${governanceReport.data.model_stack.llm_status === 'active' ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {governanceReport.data.model_stack.llm_status}
                  </span>
                </div>
              </div>
            </motion.div>

            <div className="text-xs text-ink-500 text-right">
              Report generated at: {new Date(governanceReport.data.report_generated_at).toLocaleString()}
            </div>
          </div>
        ) : (
          <EmptyState message="Unable to load governance report." />
        )}
      </Panel>
    </div>
  )
}