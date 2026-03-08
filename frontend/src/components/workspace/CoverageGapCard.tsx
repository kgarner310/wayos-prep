import { useState } from 'react'
import type { CoverageGap } from '../../api/types'
import { riskBg, riskColor } from '../../lib/utils'

interface CoverageGapCardProps {
  gap: CoverageGap
}

export function CoverageGapCard({ gap }: CoverageGapCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`border rounded-lg overflow-hidden ${riskBg(gap.risk_level)}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-3 py-2.5 flex items-center justify-between cursor-pointer"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold ${riskColor(gap.risk_level)}`}>
              {gap.coverage}
            </span>
            <span className={`text-[10px] uppercase font-medium ${riskColor(gap.risk_level)}`}>
              {gap.risk_level}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5 truncate">{gap.reason}</p>
        </div>
        <div className="flex-none ml-2 text-xs text-slate-600">
          <span className="font-mono">{Math.round(gap.confidence * 100)}%</span>
          <span className="ml-1">{expanded ? '▾' : '▸'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-slate-700/30">
          {gap.why_this_is_here.length > 0 && (
            <div className="mt-2">
              <div className="text-[10px] font-medium text-slate-500 uppercase mb-1">Why this matters</div>
              {gap.why_this_is_here.map((reason, i) => (
                <div key={i} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                  <span className="text-slate-600 mt-0.5">&#9656;</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          )}

          {gap.applied_rules.length > 0 && (
            <div>
              <div className="text-[10px] font-medium text-slate-500 uppercase mb-1">Applied Rules</div>
              {gap.applied_rules.map((rule, i) => (
                <div key={i} className="text-[11px] text-slate-500 flex items-start gap-1.5">
                  <code className="text-[10px] text-slate-600 font-mono">{rule.code}</code>
                  <span className="text-slate-400">{rule.description}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
