import type { Account } from '../../api/types'
import { cn } from '../../lib/utils'

interface AccountCardProps {
  account: Account
  isSelected: boolean
  onClick: () => void
}

export function AccountCard({ account, isSelected, onClick }: AccountCardProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-2.5 border-b border-slate-800/50 transition-colors cursor-pointer',
        isSelected
          ? 'bg-blue-500/10 border-l-2 border-l-blue-400'
          : 'hover:bg-slate-800/50 border-l-2 border-l-transparent',
      )}
    >
      <div className="text-sm font-medium text-slate-200 truncate">{account.account_name}</div>
      <div className="flex items-center gap-1.5 mt-0.5">
        <span className="text-[10px] text-slate-500">{account.industry}</span>
        <span className="text-[10px] text-slate-700">&middot;</span>
        <span className="text-[10px] text-slate-500">{account.state}</span>
      </div>
    </button>
  )
}
