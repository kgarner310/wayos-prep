interface RecommendedActionsProps {
  actions: string[]
}

export function RecommendedActions({ actions }: RecommendedActionsProps) {
  if (actions.length === 0) return null

  return (
    <div>
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-2">Recommended Actions</div>
      <div className="space-y-1">
        {actions.map((action, i) => (
          <div key={i} className="flex items-start gap-2 text-[11px]">
            <span className="text-green-500 mt-0.5">&#10003;</span>
            <span className="text-slate-300">{action}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
