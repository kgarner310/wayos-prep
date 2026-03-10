import { useState, useEffect } from 'react'
import type { PITStats } from '../../api/types'
import { getPITStats } from '../../api/client'

export function PITStatsBar() {
  const [stats, setStats] = useState<PITStats | null>(null)

  useEffect(() => {
    getPITStats().then(setStats).catch(console.error)
  }, [])

  if (!stats) return null

  const items = [
    { label: 'Pending', value: stats.pending_triage, color: 'text-yellow-400' },
    { label: 'Urgent', value: stats.urgent_count, color: stats.urgent_count > 0 ? 'text-red-400' : 'text-slate-500' },
    { label: 'Dispatched Today', value: stats.dispatches_today, color: 'text-green-400' },
    { label: 'Accounts', value: stats.accounts_touched, color: 'text-blue-400' },
  ]

  return (
    <div className="flex items-center gap-6 px-4 py-2 bg-slate-900/80 border-b border-slate-800">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <span className={`text-sm font-bold tabular-nums ${item.color}`}>{item.value}</span>
          <span className="text-[10px] text-slate-600 uppercase tracking-wide">{item.label}</span>
        </div>
      ))}
    </div>
  )
}
