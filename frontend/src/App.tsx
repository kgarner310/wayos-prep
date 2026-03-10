import { useState } from 'react'
import { AuthContext, useAuthState } from './hooks/useAuth'
import { LoginForm } from './components/auth/LoginForm'
import { AppShell } from './components/layout/AppShell'
import { AccountList } from './components/accounts/AccountList'
import { WorkspacePage } from './components/workspace/WorkspacePage'
import { TriageInbox } from './components/triage/TriageInbox'
import type { Account } from './api/types'

type AppView = 'workspace' | 'triage'

function AuthenticatedApp() {
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)
  const [view, setView] = useState<AppView>('workspace')

  return (
    <AppShell
      sidebar={
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <div className="flex-none border-b border-slate-800 p-2">
            <div className="flex gap-1">
              <button
                onClick={() => setView('workspace')}
                className={`flex-1 px-2 py-1.5 text-[11px] font-medium rounded transition-colors cursor-pointer ${
                  view === 'workspace'
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                }`}
              >
                Workspace
              </button>
              <button
                onClick={() => setView('triage')}
                className={`flex-1 px-2 py-1.5 text-[11px] font-medium rounded transition-colors cursor-pointer ${
                  view === 'triage'
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                }`}
              >
                Service Triage
              </button>
            </div>
          </div>
          {/* Sidebar content */}
          {view === 'workspace' && (
            <AccountList
              selectedId={selectedAccount?.id ?? null}
              onSelect={setSelectedAccount}
            />
          )}
          {view === 'triage' && (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-[10px] text-slate-600 text-center leading-relaxed">
                Service Triage Inbox — AI-powered request triage with one-click draft messages
              </p>
            </div>
          )}
        </div>
      }
    >
      {view === 'triage' ? (
        <TriageInbox />
      ) : selectedAccount ? (
        <WorkspacePage account={selectedAccount} />
      ) : (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-lg font-bold text-slate-300 mb-2">
              WAYOS <span className="text-blue-400">PREP</span>
            </div>
            <p className="text-sm text-slate-500 mb-4">
              Select an account or load demo data to begin
            </p>
            <div className="text-xs text-slate-600 max-w-xs mx-auto leading-relaxed">
              Insurance intelligence terminal for commercial P&amp;C producers.
              Coverage gaps, risk scoring, underwriter narratives, and competitive positioning — all in one screen.
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}

export default function App() {
  const auth = useAuthState()

  return (
    <AuthContext.Provider value={auth}>
      {auth.isAuthenticated ? <AuthenticatedApp /> : <LoginForm />}
    </AuthContext.Provider>
  )
}
