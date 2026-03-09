import { useState } from 'react'
import { AuthContext, useAuthState } from './hooks/useAuth'
import { LoginForm } from './components/auth/LoginForm'
import { AppShell } from './components/layout/AppShell'
import { AccountList } from './components/accounts/AccountList'
import { WorkspacePage } from './components/workspace/WorkspacePage'
import type { Account } from './api/types'

function AuthenticatedApp() {
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)

  return (
    <AppShell
      sidebar={
        <AccountList
          selectedId={selectedAccount?.id ?? null}
          onSelect={setSelectedAccount}
        />
      }
    >
      {selectedAccount ? (
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
