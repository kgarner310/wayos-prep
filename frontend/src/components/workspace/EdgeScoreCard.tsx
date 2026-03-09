import type { EdgeScoreResponse } from '../../api/types'
import { scoreColor } from '../../lib/utils'

interface EdgeScoreCardProps {
  edge: EdgeScoreResponse
}

export function EdgeScoreCard({ edge }: EdgeScoreCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Competitive Edge</div>

      <div className="flex items-center gap-3 mb-3">
        <div
          className="text-2xl font-bold font-mono"
          style={{ color: scoreColor(edge.overall_score) }}
        >
          {edge.overall_score}
        </div>
        <div>
          <div className="text-xs text-slate-300 font-medium capitalize">{edge.band}</div>
          <div className="text-[10px] text-slate-500">positioning</div>
        </div>
      </div>

      {edge.summary && (
        <p className="text-[11px] text-slate-400 mb-2 leading-relaxed">{edge.summary}</p>
      )}

      {edge.drivers.length > 0 && (
        <div className="space-y-0.5 mb-2">
          {edge.drivers.slice(0, 3).map((d, i) => (
            <div key={i} className="text-[11px] text-green-400">+ {d}</div>
          ))}
        </div>
      )}

      {edge.drags.length > 0 && (
        <div className="space-y-0.5">
          {edge.drags.slice(0, 3).map((d, i) => (
            <div key={i} className="text-[11px] text-red-400">- {d}</div>
          ))}
        </div>
      )}
    </div>
  )
}
