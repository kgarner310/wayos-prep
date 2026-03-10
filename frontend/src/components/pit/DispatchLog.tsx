import { useState, useEffect } from 'react'
import type { DispatchRecord } from '../../api/types'
import { getPITDispatches } from '../../api/client'

const RECIPIENT_BADGES: Record<string, { label: string; color: string }> = {
  insured: { label: 'Insured', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  carrier: { label: 'Carrier', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
  internal: { label: 'AMS', color: 'bg-slate-500/20 text-slate-400 border-slate-500/30' },
}

const CHANNEL_ICONS: Record<string, string> = {
  email: '\u2709',
  ams_note: '\uD83D\uDCCB',
  manual: '\u270D',
}

interface DispatchLogProps {
  accountId?: string
  refreshKey?: number
}

export function DispatchLog({ accountId, refreshKey }: DispatchLogProps) {
  const [dispatches, setDispatches] = useState<DispatchRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getPITDispatches(accountId)
      .then((resp) => setDispatches(resp.dispatches))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [accountId, refreshKey])

  if (loading) {
    return (
      <div className="space-y-2 p-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-14 bg-slate-800/40 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (dispatches.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-xs text-slate-600">No dispatches yet</p>
        <p className="text-[10px] text-slate-700 mt-1">Approve a triaged request to create dispatches</p>
      </div>
    )
  }

  return (
    <div className="space-y-1.5 p-2">
      {dispatches.map((d) => {
        const badge = RECIPIENT_BADGES[d.recipient_type] || RECIPIENT_BADGES.internal
        const channelIcon = CHANNEL_ICONS[d.channel] || CHANNEL_ICONS.manual

        return (
          <div
            key={d.id}
            className="p-2.5 bg-slate-900/60 border border-slate-800 rounded-md hover:border-slate-700 transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs">{channelIcon}</span>
              <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${badge.color}`}>
                {badge.label}
              </span>
              <span className="text-[10px] text-slate-600 ml-auto">
                {new Date(d.dispatched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            {d.subject && (
              <p className="text-xs text-slate-300 truncate">{d.subject}</p>
            )}
            <p className="text-[11px] text-slate-500 truncate mt-0.5">
              {d.body.slice(0, 80)}{d.body.length > 80 ? '...' : ''}
            </p>
          </div>
        )
      })}
    </div>
  )
}
