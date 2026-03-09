import { useState, useEffect, useCallback } from 'react'
import type { Account } from '../../api/types'
import * as api from '../../api/client'
import { AccountCard } from './AccountCard'

interface AccountListProps {
  selectedId: string | null
  onSelect: (account: Account) => void
}

export function AccountList({ selectedId, onSelect }: AccountListProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSeeding, setIsSeeding] = useState(false)

  const loadAccounts = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await api.listAccounts(50)
      setAccounts(res.accounts || [])
    } catch {
      // Will show empty state
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAccounts()
  }, [loadAccounts])

  const handleSeed = async () => {
    setIsSeeding(true)
    try {
      await api.seedDemoAccounts()
      await loadAccounts()
      api.trackDemoEvent('demo_seeded')
    } catch {
      // ignore
    } finally {
      setIsSeeding(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-none px-3 py-2 border-b border-slate-800">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Accounts</div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="px-3 py-4 text-xs text-slate-600">Loading...</div>
        ) : accounts.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <svg className="mx-auto mb-2 text-slate-700" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            <div className="text-xs text-slate-600 mb-1">No accounts yet</div>
            <div className="text-[10px] text-slate-700">Load demo data below to get started</div>
          </div>
        ) : (
          accounts.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              isSelected={account.id === selectedId}
              onClick={() => onSelect(account)}
            />
          ))
        )}
      </div>

      <div className="flex-none p-2 border-t border-slate-800 space-y-1">
        <button
          onClick={handleSeed}
          disabled={isSeeding}
          className="w-full py-1.5 text-xs font-medium text-blue-400 hover:text-blue-300
                     bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20
                     rounded transition-colors disabled:opacity-50 cursor-pointer"
        >
          {isSeeding ? 'Loading demos...' : 'Load Demo Accounts'}
        </button>
      </div>
    </div>
  )
}
