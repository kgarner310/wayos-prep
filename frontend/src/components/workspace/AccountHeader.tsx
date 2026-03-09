import type { AccountSummary } from '../../api/types'

interface AccountHeaderProps {
  summary: AccountSummary
}

export function AccountHeader({ summary }: AccountHeaderProps) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-bold text-slate-100 tracking-tight">{summary.account_name}</h2>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-xs text-slate-400">{summary.industry}</span>
        <span className="text-slate-700">&middot;</span>
        <span className="text-xs text-slate-400">{summary.state}</span>
        <span className="text-slate-700">&middot;</span>
        <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium bg-blue-500/15 text-blue-400 rounded uppercase">
          {summary.account_stage}
        </span>
      </div>
      {summary.key_facts.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {summary.key_facts.map((fact, i) => (
            <span key={i} className="text-[11px] text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded">
              {fact}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
