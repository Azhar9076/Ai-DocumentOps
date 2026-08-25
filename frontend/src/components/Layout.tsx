import { NavLink, Outlet } from 'react-router-dom'
import { BarChart3, FileStack, GaugeCircle, UploadCloud, Workflow, Shield } from 'lucide-react'
import { ErrorBoundary } from './ErrorBoundary'

const NAV = [
  { to: '/', label: 'Executive Dashboard', Icon: BarChart3, end: true },
  { to: '/upload', label: 'Upload & Process', Icon: UploadCloud },
  { to: '/queue', label: 'Review Queue', Icon: FileStack },
  { to: '/workflow', label: 'How It Works', Icon: Workflow },
  { to: '/quality', label: 'Accuracy & Quality', Icon: GaugeCircle },
  { to: '/governance', label: 'IBM Governance & Trust', Icon: Shield },
]

export function Layout() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-[1600px] gap-6 p-6">
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-64 shrink-0 flex-col lg:flex">
          <div className="glass flex h-full flex-col p-5">
            <div className="mb-8 flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-900 text-sm font-bold text-white">
                AD
              </div>
              <div>
                <p className="text-sm font-semibold leading-tight">AI DocumentOps</p>
                <p className="text-xs text-ink-500">Document automation</p>
              </div>
            </div>
            
            {/* IBM Status Badges */}
            <div className="mb-6 flex flex-wrap gap-2">
              <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 border border-emerald-200">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500"></div>
                IBM Docling
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 border border-blue-200">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                IBM Granite 3.0
              </div>
            </div>
            <nav className="flex flex-1 flex-col gap-1">
              {NAV.map(({ to, label, Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                      isActive
                        ? 'bg-ink-900 text-white shadow-panel'
                        : 'text-ink-700 hover:bg-white/70'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
            <p className="mt-6 text-xs leading-relaxed text-ink-500">
              Confidence routing: <span className="font-medium text-emerald-700">≥90% auto</span>,{' '}
              <span className="font-medium text-amber-700">70–89% review</span>,{' '}
              <span className="font-medium text-rose-700">&lt;70% action</span>.
            </p>
          </div>
        </aside>
        <main className="min-w-0 flex-1">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
