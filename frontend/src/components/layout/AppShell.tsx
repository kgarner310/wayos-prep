import { type ReactNode, useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../hooks/useAuth'

interface AppShellProps {
  sidebar: ReactNode
  children: ReactNode
}

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : true,
  )

  useEffect(() => {
    const mql = window.matchMedia(query)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [query])

  return matches
}

export function AppShell({ sidebar, children }: AppShellProps) {
  const { user, logout } = useAuth()
  const isLargeScreen = useMediaQuery('(min-width: 1024px)')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Auto-close sidebar on small screens
  useEffect(() => {
    setSidebarOpen(isLargeScreen)
  }, [isLargeScreen])

  const closeSidebar = useCallback(() => {
    if (!isLargeScreen) setSidebarOpen(false)
  }, [isLargeScreen])

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top bar */}
      <header className="flex-none h-12 flex items-center justify-between px-4 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-slate-200 transition-colors cursor-pointer lg:hidden"
            aria-label="Toggle sidebar"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          </button>
          <h1 className="text-sm font-bold tracking-tight">
            WAYOS <span className="text-blue-400">PREP</span>
          </h1>
          <span className="text-[10px] text-slate-600 font-mono">v0.3</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 hidden sm:inline">{user?.email}</span>
          <button
            onClick={logout}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Overlay backdrop for mobile */}
        {sidebarOpen && !isLargeScreen && (
          <div
            className="absolute inset-0 bg-black/40 z-20"
            onClick={closeSidebar}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            ${isLargeScreen ? 'relative' : 'absolute left-0 top-0 bottom-0 z-30'}
            ${sidebarOpen ? 'w-56' : 'w-0'}
            bg-slate-900/95 border-r border-slate-800 flex flex-col overflow-hidden
            transition-[width] duration-200 ease-in-out flex-none
          `}
          onClick={closeSidebar}
        >
          {sidebarOpen && (
            <div className="w-56 h-full flex flex-col" onClick={(e) => e.stopPropagation()}>
              {sidebar}
            </div>
          )}
        </aside>

        {/* Main workspace */}
        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
      </div>
    </div>
  )
}
