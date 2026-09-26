import { NavLink, Outlet } from 'react-router-dom'
import {
  BarChart3,
  FileStack,
  GaugeCircle,
  ShieldCheck,
  UploadCloud,
  UserCheck,
  Workflow,
  Zap,
} from 'lucide-react'
import { useAuth } from '../lib/authContext'
import { ErrorBoundary } from './ErrorBoundary'

export function Layout() {
  const { role, setRole, isAdmin } = useAuth()

  const navItems = [
    ...(isAdmin ? [{ to: '/', label: 'Executive Dashboard', Icon: BarChart3, end: true }] : []),
    { to: '/upload', label: 'Upload & Process', Icon: UploadCloud },
    { to: '/queue', label: 'Review Queue', Icon: FileStack },
    { to: '/workflow', label: 'How It Works', Icon: Workflow },
    ...(isAdmin ? [{ to: '/quality', label: 'Accuracy & Quality', Icon: GaugeCircle }] : []),
    ...(isAdmin ? [{ to: '/stress-test', label: 'Intake Stress-Test', Icon: Zap }] : []),
    { to: '/governance', label: 'IBM Governance & Trust', Icon: ShieldCheck },
  ]

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-[1600px] gap-6 p-6">
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-64 shrink-0 flex-col lg:flex">
          <div className="glass flex h-full flex-col p-5">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-900 text-sm font-bold text-white shadow-sm">
                AD
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold leading-tight">AI DocumentOps</p>
                <p className="text-xs text-ink-500">Document automation</p>
              </div>
            </div>

            {/* Role Switcher */}
            <div className="mb-6 rounded-xl border border-ink-200 bg-white/70 p-2.5">
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-500">
                  Active Role
                </span>
                <span
                  className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium ${
                    isAdmin ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {isAdmin ? <ShieldCheck className="h-3 w-3" /> : <UserCheck className="h-3 w-3" />}
                  {role.toUpperCase()}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 rounded-lg bg-ink-100 p-0.5 text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setRole('admin')}
                  className={`rounded-md py-1 transition ${
                    isAdmin ? 'bg-white text-ink-900 shadow-sm' : 'text-ink-600 hover:text-ink-900'
                  }`}
                >
                  Admin
                </button>
                <button
                  type="button"
                  onClick={() => setRole('reviewer')}
                  className={`rounded-md py-1 transition ${
                    !isAdmin ? 'bg-white text-ink-900 shadow-sm' : 'text-ink-600 hover:text-ink-900'
                  }`}
                >
                  Reviewer
                </button>
              </div>
            </div>

            <nav className="flex flex-1 flex-col gap-1">
              {navItems.map(({ to, label, Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                      isActive
                        ? 'bg-ink-900 text-white shadow-panel font-medium'
                        : 'text-ink-700 hover:bg-white/70'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>

            <div className="mt-auto border-t border-ink-200/70 pt-4">
              <p className="text-[11px] leading-relaxed text-ink-500">
                <span className="font-semibold text-ink-700">Granite 3.0 Agents:</span>
                <br />
                <span className="font-medium text-emerald-700">≥90% auto-pass</span> ·{' '}
                <span className="font-medium text-amber-700">70–89% review</span> ·{' '}
                <span className="font-medium text-rose-700">&lt;70% action</span>
              </p>
            </div>
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
