import type { MarketSignalsResponse } from '../../api/types'

interface MarketSignalsCardProps {
  signals: MarketSignalsResponse
}

export function MarketSignalsCard({ signals }: MarketSignalsCardProps) {
  const topLossReasons = Object.entries(signals.loss_reasons)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)

  const maxLossCount = topLossReasons.length > 0 ? topLossReasons[0][1] : 1

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Market Signals</div>

      <div className="flex items-center gap-3 mb-3">
        <div className="text-2xl font-bold font-mono text-blue-400">
          {Math.round(signals.win_rate_overall * 100)}%
        </div>
        <div>
          <div className="text-xs text-slate-300 font-medium">Win Rate</div>
          <div className="text-[10px] text-slate-500">{signals.total_outcomes} outcomes</div>
        </div>
      </div>

      {signals.top_carrier && (
        <div className="text-[11px] text-slate-400 mb-2">
          Top carrier: <span className="text-slate-300 font-medium">{signals.top_carrier}</span>
        </div>
      )}

      {topLossReasons.length > 0 && (
        <div className="space-y-1 mt-2">
          <div className="text-[10px] text-slate-600 uppercase">Loss Reasons</div>
          {topLossReasons.map(([reason, count]) => (
            <div key={reason} className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500/50 rounded-full"
                  style={{ width: `${(count / maxLossCount) * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500 w-14 truncate">{reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
