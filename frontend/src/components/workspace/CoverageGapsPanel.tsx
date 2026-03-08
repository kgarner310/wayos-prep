import type { CoverageGap } from '../../api/types'
import { CoverageGapCard } from './CoverageGapCard'

interface CoverageGapsPanelProps {
  gaps: CoverageGap[]
}

export function CoverageGapsPanel({ gaps }: CoverageGapsPanelProps) {
  const sorted = [...gaps].sort((a, b) => {
    const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }
    return (order[a.risk_level] ?? 4) - (order[b.risk_level] ?? 4)
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Coverage Gaps</div>
        <div className="text-[10px] text-slate-600 font-mono">{gaps.length} identified</div>
      </div>
      <div className="space-y-2">
        {sorted.map((gap, i) => (
          <CoverageGapCard key={i} gap={gap} />
        ))}
      </div>
    </div>
  )
}
