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
          <div className="px-3 py-4 text-xs text-slate-600">No accounts yet</div>
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
