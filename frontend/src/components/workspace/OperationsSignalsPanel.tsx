import type { OperationsSignals } from '../../api/types'

interface OperationsSignalsPanelProps {
  signals: OperationsSignals
}

function SignalGroup({ label, items, color }: { label: string; items: string[]; color: string }) {
  if (items.length === 0) return null
  return (
    <div className="mb-3">
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</div>
      <div className="space-y-0.5">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-1.5 text-[11px]">
            <span className={`mt-0.5 ${color}`}>&#9679;</span>
            <span className="text-slate-300">{item}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function OperationsSignalsPanel({ signals }: OperationsSignalsPanelProps) {
  const totalSignals =
    signals.operations_signals.length +
    signals.safety_signals.length +
    signals.scale_signals.length +
    signals.carrier_relevant_signals.length

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Operations Intel</div>
        <div className="text-[10px] text-slate-600 font-mono">{totalSignals} signals</div>
      </div>

      {signals.company_identity.company_name && (
        <div className="mb-3 px-2 py-1.5 bg-slate-800/40 rounded text-[11px] text-slate-400">
          <span className="text-slate-300 font-medium">{signals.company_identity.company_name}</span>
          {signals.company_identity.founded_year && (
            <span> &middot; Est. {signals.company_identity.founded_year}</span>
          )}
          {signals.company_identity.service_area.length > 0 && (
            <span> &middot; {signals.company_identity.service_area.join(', ')}</span>
          )}
        </div>
      )}

      <SignalGroup label="Operations" items={signals.operations_signals} color="text-blue-400" />
      <SignalGroup label="Safety" items={signals.safety_signals} color="text-green-400" />
      <SignalGroup label="Scale" items={signals.scale_signals} color="text-purple-400" />
      <SignalGroup label="Carrier Relevant" items={signals.carrier_relevant_signals} color="text-yellow-400" />
    </div>
  )
}
