import { useState, useEffect, useCallback } from 'react'
import type { TriageRequest, TriageStatus } from '../../api/types'
import { listTriageRequests } from '../../api/client'
import { TriageRequestForm } from './TriageRequestForm'
import { TriageDetail } from './TriageDetail'

const STATUS_TABS: { label: string; value: string | undefined }[] = [
  { label: 'All', value: undefined },
  { label: 'Pending', value: 'pending' },
  { label: 'Triaged', value: 'triaged' },
  { label: 'Approved', value: 'approved' },
]

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
  rejected: 'bg-red-500/20 text-red-400',
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

export function TriageInbox() {
  const [requests, setRequests] = useState<TriageRequest[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const loadRequests = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await listTriageRequests(statusFilter)
      setRequests(resp.requests)
      setTotal(resp.total)
    } catch (err) {
      console.error('Failed to load triage requests:', err)
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadRequests()
  }, [loadRequests])

  const selected = requests.find((r) => r.id === selectedId) ?? null

  if (showForm) {
    return (
      <TriageRequestForm
        onSubmit={() => {
          setShowForm(false)
          loadRequests()
        }}
        onCancel={() => setShowForm(false)}
      />
    )
  }

  if (selected) {
    return (
      <TriageDetail
        request={selected}
        onBack={() => {
          setSelectedId(null)
          loadRequests()
        }}
        onUpdate={loadRequests}
      />
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Service Triage</h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-powered service request triage &mdash; draft messages to insureds, carriers, and AMS in one click
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
        >
          + New Request
        </button>
      </div>

      {/* Status Tabs */}
      <div className="flex gap-1 mb-4 border-b border-slate-800 pb-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.label}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              statusFilter === tab.value
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-600 self-center">{total} total</span>
      </div>

      {/* Request List */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-slate-800/50 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : requests.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-slate-500 text-sm mb-4">No service requests yet</p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition-colors cursor-pointer"
          >
            Create your first request
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {requests.map((req) => (
            <button
              key={req.id}
              onClick={() => setSelectedId(req.id)}
              className="w-full text-left p-4 bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-lg transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {req.urgency && (
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${URGENCY_COLORS[req.urgency] || URGENCY_COLORS.medium}`}>
                        {req.urgency.toUpperCase()}
                      </span>
                    )}
                    {req.request_type && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        {TYPE_LABELS[req.request_type] || req.request_type}
                      </span>
                    )}
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${STATUS_COLORS[req.status] || STATUS_COLORS.pending}`}>
                      {req.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 truncate">
                    {req.summary || req.input_text.slice(0, 120)}
                  </p>
                  {req.input_filename && (
                    <p className="text-xs text-slate-600 mt-1">
                      Attached: {req.input_filename}
                    </p>
                  )}
                </div>
                <div className="text-right flex-none">
                  <p className="text-[10px] text-slate-600">
                    {new Date(req.created_at).toLocaleDateString()}
                  </p>
                  <p className="text-[10px] text-slate-700">
                    {new Date(req.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
