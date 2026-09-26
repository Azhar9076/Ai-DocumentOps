'use client'

import { useState } from 'react'
import { BarChart3, FileStack, ShieldCheck } from 'lucide-react'
import { GovernanceTrustTab } from '../components/GovernanceTrustTab'
import { Dashboard } from '../pages/Dashboard'
import { Quality } from '../pages/Quality'

export default function Page() {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'accuracy' | 'governance'>('pipeline')

  return (
    <div className="space-y-6">
      {/* Top Level Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-ink-200/80 pb-4">
        <button
          type="button"
          onClick={() => setActiveTab('pipeline')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
            activeTab === 'pipeline'
              ? 'bg-ink-900 text-white shadow-md'
              : 'bg-white/70 text-ink-700 hover:bg-white'
          }`}
        >
          <FileStack className="h-4 w-4" />
          Pipeline &amp; Review
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('accuracy')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
            activeTab === 'accuracy'
              ? 'bg-ink-900 text-white shadow-md'
              : 'bg-white/70 text-ink-700 hover:bg-white'
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          Accuracy &amp; ROI Dashboard
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('governance')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
            activeTab === 'governance'
              ? 'bg-slate-900 text-emerald-400 shadow-md border border-slate-700'
              : 'bg-white/70 text-ink-700 hover:bg-white'
          }`}
        >
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          IBM Governance &amp; Trust
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'pipeline' && <Dashboard />}
      {activeTab === 'accuracy' && <Quality />}
      {activeTab === 'governance' && <GovernanceTrustTab />}
    </div>
  )
}
