import { useState, useEffect, useCallback } from 'react'
import type { PITFeedItem, TriageRequest } from '../../api/types'
import { getPITFeed, listTriageRequests } from '../../api/client'
import { PITStatsBar } from './PITStatsBar'
import { DispatchLog } from './DispatchLog'
import { TriageDetail } from '../triage/TriageDetail'
import { TriageRequestForm } from '../triage/TriageRequestForm'

const URGENCY_COLORS: Record<string, string> = {
  urgent: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-slate-600/30 text-slate-400',
  triaged: 'bg-blue-500/20 text-blue-400',
  approved: 'bg-green-500/20 text-green-400',
  logged: 'bg-green-500/20 text-green-400',
  sent: 'bg-green-500/20 text-green-400',
}

const RECIPIENT_LABELS: Record<string, string> = {
  insured: 'To Insured',
  carrier: 'To Carrier',
  internal: 'AMS Note',
}

const TYPE_LABELS: Record<string, string> = {
  certificate_request: 'Certificate',
  endorsement_change: 'Endorsement',
  claim_report: 'Claim',
  billing_inquiry: 'Billing',
  policy_question: 'Policy Q',
  renewal: 'Renewal',
  cancellation: 'Cancel',
  audit: 'Audit',
  new_business: 'New Biz',
  other: 'Other',
}

type ViewMode = 'feed' | 'triage-detail' | 'new-request'

export function PITDashboard() {
  const [feedItems, setFeedItems] = useState<PITFeedItem[]>([])
  const [triageRequests, setTriageRequests] = useState<TriageRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<ViewMode>('feed')
  const [selectedTriageId, setSelectedTriageId] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [feedResp, triageResp] = await Promise.all([
        getPITFeed(),
        listTriageRequests(),
      ])
      setFeedItems(feedResp.items)
      setTriageRequests(triageResp.requests)
    } catch (err) {
      console.error('Failed to load PIT data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData, refreshKey])

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1)
  }

  const selectedTriage = triageRequests.find((r) => r.id === selectedTriageId) ?? null

  // Triage detail view
  if (viewMode === 'triage-detail' && selectedTriage) {
    return (
      <div className="h-full flex flex-col">
        <PITStatsBar />
        <div className="flex-1 overflow-auto p-6">
          <TriageDetail
            request={selectedTriage}
            onBack={() => {
              setViewMode('feed')
              setSelectedTriageId(null)
              handleRefresh()
            }}
            onUpdate={handleRefresh}
          />
        </div>
      </div>
    )
  }

  // New request form
  if (viewMode === 'new-request') {
    return (
      <div className="h-full flex flex-col">
        <PITStatsBar />
        <div className="flex-1 overflow-auto p-6">
          <TriageRequestForm
            onSubmit={() => {
              setViewMode('feed')
              handleRefresh()
            }}
            onCancel={() => setViewMode('feed')}
          />
        </div>
      </div>
    )
  }

  // Main PIT feed view
  return (
    <div className="h-full flex flex-col">
      <PITStatsBar />

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Feed */}
        <div className="flex-1 overflow-auto border-r border-slate-800">
          {/* Header */}
          <div className="sticky top-0 bg-slate-950/95 backdrop-blur-sm z-10 px-4 py-3 border-b border-slate-800">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-base font-bold text-slate-100">Producer Intel Terminal</h1>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  Triage + Dispatch — unified service command center
                </p>
              </div>
              <button
                onClick={() => setViewMode('new-request')}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-md transition-colors cursor-pointer"
              >
                + New Request
              </button>
            </div>
          </div>

          {/* Feed items */}
          <div className="p-3">
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-16 bg-slate-800/40 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : feedItems.length === 0 ? (
              <div className="text-center py-16">
                <p className="text-slate-500 text-sm mb-2">No activity yet</p>
                <p className="text-xs text-slate-600">Create a service request to get started</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {feedItems.map((item) => (
                  <button
                    key={`${item.item_type}-${item.item_id}`}
                    onClick={() => {
                      if (item.item_type === 'triage') {
                        setSelectedTriageId(item.item_id)
                        setViewMode('triage-detail')
                      }
                    }}
                    className={`w-full text-left p-3 bg-slate-900/60 border border-slate-800 rounded-lg transition-all ${
                      item.item_type === 'triage'
                        ? 'hover:bg-slate-800/80 hover:border-slate-700 cursor-pointer'
                        : 'cursor-default'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-1">
                          {/* Type indicator */}
                          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                            item.item_type === 'triage'
                              ? 'bg-blue-500/10 text-blue-500'
                              : 'bg-green-500/10 text-green-500'
                          }`}>
                            {item.item_type === 'triage' ? 'TRI' : 'DIS'}
                          </span>

                          {/* Urgency badge (triage only) */}
                          {item.urgency && (
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                              URGENCY_COLORS[item.urgency] || URGENCY_COLORS.medium
                            }`}>
                              {item.urgency.toUpperCase()}
                            </span>
                          )}

                          {/* Request type or recipient type */}
                          {item.request_type && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              {TYPE_LABELS[item.request_type] || item.request_type}
                            </span>
                          )}
                          {item.recipient_type && (
                            <span className="text-[10px] text-slate-500">
                              {RECIPIENT_LABELS[item.recipient_type] || item.recipient_type}
                            </span>
                          )}

                          {/* Status */}
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                            STATUS_COLORS[item.status] || STATUS_COLORS.pending
                          }`}>
                            {item.status}
                          </span>
                        </div>
                        <p className="text-sm text-slate-200 truncate">{item.summary}</p>
                      </div>
                      <div className="text-right flex-none">
                        <p className="text-[10px] text-slate-600">
                          {new Date(item.timestamp).toLocaleDateString()}
                        </p>
                        <p className="text-[10px] text-slate-700">
                          {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Dispatch Log */}
        <div className="w-72 flex-none overflow-auto">
          <div className="sticky top-0 bg-slate-950/95 backdrop-blur-sm z-10 px-3 py-2.5 border-b border-slate-800">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Dispatch Log</h2>
          </div>
          <DispatchLog refreshKey={refreshKey} />
        </div>
      </div>
    </div>
  )
}
