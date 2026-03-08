import type { SubmissionReadinessResponse } from '../../api/types'
import { scoreColor } from '../../lib/utils'

interface SubmissionReadinessCardProps {
  readiness: SubmissionReadinessResponse
  onBuildPacket: () => void
  isLoadingPacket: boolean
}

function levelColor(level: string): string {
  switch (level) {
    case 'strong': return 'text-green-400 bg-green-500/10 border-green-500/20'
    case 'good': return 'text-blue-400 bg-blue-500/10 border-blue-500/20'
    case 'fair': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
    case 'poor': return 'text-red-400 bg-red-500/10 border-red-500/20'
    default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20'
  }
}

export function SubmissionReadinessCard({ readiness, onBuildPacket, isLoadingPacket }: SubmissionReadinessCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Submission Readiness</div>

      <div className="flex items-center gap-4 mb-3">
        {/* Score */}
        <div className="flex-none">
          <div className="text-3xl font-bold font-mono" style={{ color: scoreColor(readiness.readiness_score) }}>
            {readiness.readiness_score}
          </div>
          <div className="text-[10px] text-slate-600 text-center">/ 100</div>
        </div>

        {/* Level badge + explanation */}
        <div className="flex-1">
          <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded border uppercase mb-1 ${levelColor(readiness.readiness_level)}`}>
            {readiness.readiness_level}
          </span>
          {readiness.explanation && (
            <p className="text-[11px] text-slate-400 leading-relaxed">{readiness.explanation}</p>
          )}
        </div>
      </div>

      {/* Missing critical fields */}
      {readiness.missing_critical_fields.length > 0 && (
        <div className="mb-2">
          <div className="text-[10px] text-red-400 font-medium uppercase mb-1">Missing Critical</div>
          <div className="flex flex-wrap gap-1">
            {readiness.missing_critical_fields.map((field, i) => (
              <span key={i} className="text-[10px] text-red-300 bg-red-500/10 px-1.5 py-0.5 rounded">
                {field}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Strengths */}
      {readiness.strengths.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] text-green-400/70 font-medium uppercase mb-1">Strengths</div>
          <div className="space-y-0.5">
            {readiness.strengths.slice(0, 3).map((s, i) => (
              <div key={i} className="text-[11px] text-green-400/60">+ {s}</div>
            ))}
          </div>
        </div>
      )}

      {/* Next steps */}
      {readiness.next_steps.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] text-slate-500 font-medium uppercase mb-1">Next Steps</div>
          <div className="space-y-0.5">
            {readiness.next_steps.slice(0, 3).map((step, i) => (
              <div key={i} className="text-[11px] text-slate-400">&#8594; {step}</div>
            ))}
          </div>
        </div>
      )}

      {/* Build packet button */}
      <button
        onClick={onBuildPacket}
        disabled={isLoadingPacket}
        className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500
                   text-white text-xs font-medium rounded transition-colors cursor-pointer mt-1"
      >
        {isLoadingPacket ? 'Building Packet...' : 'Build Submission Packet'}
      </button>
    </div>
  )
}
