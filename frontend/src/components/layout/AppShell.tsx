import { type ReactNode } from 'react'
import { useAuth } from '../../hooks/useAuth'

interface AppShellProps {
  sidebar: ReactNode
  children: ReactNode
}

export function AppShell({ sidebar, children }: AppShellProps) {
  const { user, logout } = useAuth()

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top bar */}
      <header className="flex-none h-12 flex items-center justify-between px-4 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-bold tracking-tight">
            WAYOS <span className="text-blue-400">PREP</span>
          </h1>
          <span className="text-[10px] text-slate-600 font-mono">v0.3</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">{user?.email}</span>
          <button
            onClick={logout}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="flex-none w-56 bg-slate-900/50 border-r border-slate-800 flex flex-col overflow-hidden">
          {sidebar}
        </aside>

        {/* Main workspace */}
        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
      </div>
    </div>
  )
}
