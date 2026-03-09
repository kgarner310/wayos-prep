import type { RiskOverview } from '../../api/types'
import { riskBg, riskColor, confidenceLabel } from '../../lib/utils'

interface RiskOverviewCardProps {
  risk: RiskOverview
}

export function RiskOverviewCard({ risk }: RiskOverviewCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Risk Assessment</div>

      <div className="flex items-center gap-3 mb-3">
        <span
          className={`inline-flex items-center px-2.5 py-1 text-xs font-bold rounded border uppercase ${riskBg(risk.risk_level)} ${riskColor(risk.risk_level)}`}
        >
          {risk.risk_level}
        </span>
        <div className="text-[11px] text-slate-500">
          {confidenceLabel(risk.confidence)} confidence ({Math.round(risk.confidence * 100)}%)
        </div>
      </div>

      {risk.headline && (
        <p className="text-xs text-slate-300 mb-3 leading-relaxed">{risk.headline}</p>
      )}

      {risk.contributing_factors.length > 0 && (
        <div className="space-y-1">
          {risk.contributing_factors.slice(0, 4).map((factor, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[11px] text-slate-400">
              <span className="text-slate-600 mt-0.5">&#9656;</span>
              <span>{factor}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
