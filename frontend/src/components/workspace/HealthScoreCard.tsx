import type { AccountHealth } from '../../api/types'
import { scoreColor } from '../../lib/utils'

interface HealthScoreCardProps {
  health: AccountHealth
}

function ScoreCircle({ value, size = 64 }: { value: number; size?: number }) {
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (value / 100) * circumference
  const color = scoreColor(value)

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={4}
        className="text-slate-800"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={4}
        strokeDasharray={circumference}
        strokeDashoffset={circumference - progress}
        strokeLinecap="round"
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        className="text-sm font-bold fill-slate-100"
        transform={`rotate(90, ${size / 2}, ${size / 2})`}
      >
        {value}
      </text>
    </svg>
  )
}

function SubScore({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between text-[11px]">
      <span className="text-slate-500">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${value}%`, backgroundColor: scoreColor(value) }}
          />
        </div>
        <span className="text-slate-400 w-6 text-right font-mono">{value}</span>
      </div>
    </div>
  )
}

export function HealthScoreCard({ health }: HealthScoreCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Account Health</div>
      <div className="flex items-center gap-4">
        <ScoreCircle value={health.overall_score} />
        <div className="flex-1 space-y-1.5">
          <SubScore label="Coverage" value={health.coverage_score} />
          <SubScore label="Workers Comp" value={health.workers_comp_score} />
          <SubScore label="Carrier Fit" value={health.carrier_fit_score} />
        </div>
      </div>
      {health.duty_to_advise_alert_count > 0 && (
        <div className="mt-3 px-2 py-1 bg-red-500/10 border border-red-500/20 rounded text-[11px] text-red-400">
          {health.duty_to_advise_alert_count} duty-to-advise alert{health.duty_to_advise_alert_count > 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
