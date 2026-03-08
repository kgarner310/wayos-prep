import type { TimelineResponse } from '../../api/types'

interface TimelinePanelProps {
  timeline: TimelineResponse
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

function eventTypeLabel(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function eventTypeColor(type: string): string {
  if (type.includes('brief') || type.includes('generated')) return 'bg-blue-400'
  if (type.includes('gap') || type.includes('risk')) return 'bg-orange-400'
  if (type.includes('outcome') || type.includes('won')) return 'bg-green-400'
  if (type.includes('lost')) return 'bg-red-400'
  if (type.includes('intel') || type.includes('refresh')) return 'bg-purple-400'
  return 'bg-slate-400'
}

export function TimelinePanel({ timeline }: TimelinePanelProps) {
  if (timeline.events.length === 0) return null

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Account Timeline</div>
        <div className="text-[10px] text-slate-600 font-mono">{timeline.count} events</div>
      </div>

      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[5px] top-2 bottom-2 w-px bg-slate-800" />

        <div className="space-y-3">
          {timeline.events.slice(0, 10).map((event) => (
            <div key={event.id} className="flex items-start gap-3 relative">
              {/* Dot */}
              <div className={`flex-none w-[11px] h-[11px] rounded-full mt-0.5 ${eventTypeColor(event.event_type)} ring-2 ring-slate-900`} />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-300 font-medium">
                    {eventTypeLabel(event.event_type)}
                  </span>
                  <span className="text-[10px] text-slate-600 flex-none">
                    {formatDate(event.created_at)}
                  </span>
                </div>
                {event.notes && (
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">{event.notes}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
