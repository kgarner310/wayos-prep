import { useState, useCallback } from 'react'
import type { TriageRequest } from '../../api/types'
import { approveTriageRequest, updateTriageRequest, retriageRequest } from '../../api/client'

interface TriageDetailProps {
  request: TriageRequest
  onBack: () => void
  onUpdate: () => void
}

const URGENCY_COLORS: Record<string, string> = {
  urgent: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
}

const TYPE_LABELS: Record<string, string> = {
  certificate_request: 'Certificate of Insurance',
  endorsement_change: 'Endorsement / Policy Change',
  claim_report: 'Claim Report',
  billing_inquiry: 'Billing Inquiry',
  policy_question: 'Policy Question',
  renewal: 'Renewal',
  cancellation: 'Cancellation',
  audit: 'Audit',
  new_business: 'New Business',
  other: 'Other',
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [text])

  return (
    <button
      onClick={handleCopy}
      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer ${
        copied
          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
          : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-slate-600'
      }`}
    >
      {copied ? 'Copied!' : `Copy ${label}`}
    </button>
  )
}

function DraftCard({
  title,
  icon,
  color,
  subject,
  body,
  copyLabel,
}: {
  title: string
  icon: string
  color: string
  subject?: string
  body: string
  copyLabel: string
}) {
  const fullText = subject ? `Subject: ${subject}\n\n${body}` : body

  return (
    <div className={`border rounded-lg overflow-hidden ${color}`}>
      <div className="px-4 py-2.5 flex items-center justify-between border-b border-inherit">
        <div className="flex items-center gap-2">
          <span className="text-base">{icon}</span>
          <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        </div>
        <CopyButton text={fullText} label={copyLabel} />
      </div>
      <div className="p-4 space-y-2">
        {subject && (
          <div>
            <span className="text-[10px] text-slate-600 uppercase tracking-wide">Subject</span>
            <p className="text-sm text-slate-300 mt-0.5">{subject}</p>
          </div>
        )}
        <div>
          {subject && <span className="text-[10px] text-slate-600 uppercase tracking-wide">Body</span>}
          <p className="text-sm text-slate-400 mt-0.5 whitespace-pre-wrap leading-relaxed">{body}</p>
        </div>
      </div>
    </div>
  )
}

function AmsNoteCard({
  note,
}: {
  note: { summary: string; action_items: string[]; category: string }
}) {
  const fullText = [
    `Category: ${note.category}`,
    '',
    note.summary,
    '',
    'Action Items:',
    ...note.action_items.map((item) => `- ${item}`),
  ].join('\n')

  return (
    <div className="border border-slate-700/50 bg-slate-900/40 rounded-lg overflow-hidden">
      <div className="px-4 py-2.5 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-base">&#128203;</span>
          <h3 className="text-sm font-semibold text-slate-200">AMS Note</h3>
        </div>
        <CopyButton text={fullText} label="AMS Note" />
      </div>
      <div className="p-4 space-y-3">
        <div>
          <span className="text-[10px] text-slate-600 uppercase tracking-wide">Category</span>
          <p className="text-xs text-slate-500 mt-0.5">{note.category}</p>
        </div>
        <div>
          <span className="text-[10px] text-slate-600 uppercase tracking-wide">Summary</span>
          <p className="text-sm text-slate-400 mt-0.5">{note.summary}</p>
        </div>
        {note.action_items.length > 0 && (
          <div>
            <span className="text-[10px] text-slate-600 uppercase tracking-wide">Action Items</span>
            <ul className="mt-1 space-y-1">
              {note.action_items.map((item, i) => (
                <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">&#8226;</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export function TriageDetail({ request: req, onBack, onUpdate }: TriageDetailProps) {
  const [approving, setApproving] = useState(false)
  const [retriaging, setRetriaging] = useState(false)

  async function handleApprove() {
    setApproving(true)
    try {
      await approveTriageRequest(req.id)
      onUpdate()
      onBack()
    } catch (err) {
      console.error('Failed to approve:', err)
    } finally {
      setApproving(false)
    }
  }

  async function handleRetriage() {
    setRetriaging(true)
    try {
      await retriageRequest(req.id)
      onUpdate()
    } catch (err) {
      console.error('Failed to retriage:', err)
    } finally {
      setRetriaging(false)
    }
  }

  const isPending = req.status === 'pending'
  const isTriaged = req.status === 'triaged'
  const isApproved = req.status === 'approved'

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back + Header */}
      <div className="mb-6">
        <button
          onClick={onBack}
          className="text-xs text-slate-500 hover:text-slate-300 mb-3 transition-colors cursor-pointer"
        >
          &larr; Back to Inbox
        </button>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {req.urgency && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${URGENCY_COLORS[req.urgency] || ''}`}>
                  {req.urgency.toUpperCase()}
                </span>
              )}
              {req.request_type && (
                <span className="text-xs text-slate-500">
                  {TYPE_LABELS[req.request_type] || req.request_type}
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold text-slate-100 mt-1">
              {req.summary || 'Processing...'}
            </h2>
            <p className="text-xs text-slate-600 mt-1">
              Created {new Date(req.created_at).toLocaleString()}
              {req.confidence && (
                <span className="ml-2">
                  AI Confidence: {Math.round(req.confidence * 100)}%
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            {isTriaged && (
              <>
                <button
                  onClick={handleRetriage}
                  disabled={retriaging}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 rounded-md transition-colors cursor-pointer"
                >
                  {retriaging ? 'Re-triaging...' : 'Re-triage'}
                </button>
                <button
                  onClick={handleApprove}
                  disabled={approving}
                  className="px-4 py-1.5 text-xs font-semibold bg-green-600 hover:bg-green-500 text-white rounded-md transition-colors cursor-pointer"
                >
                  {approving ? 'Approving...' : 'Approve'}
                </button>
              </>
            )}
            {isApproved && (
              <span className="px-3 py-1.5 text-xs font-semibold bg-green-500/20 text-green-400 rounded-md">
                Approved
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Original Request */}
      <div className="mb-6 p-4 bg-slate-900/60 border border-slate-800 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] text-slate-600 uppercase tracking-wide font-semibold">
            Original Request
          </span>
          <span className="text-[10px] text-slate-700">({req.input_type})</span>
        </div>
        <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
          {req.input_text}
        </p>
        {req.input_filename && (
          <p className="text-xs text-slate-600 mt-2">
            Attached: {req.input_filename}
          </p>
        )}
      </div>

      {/* Drafts */}
      {isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-slate-800/40 rounded-lg animate-pulse" />
          ))}
          <p className="text-center text-sm text-slate-600 mt-4">
            AI is triaging this request...
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <h3 className="text-xs text-slate-600 uppercase tracking-wide font-semibold">
            Draft Messages &mdash; Review, copy, and send from your email / AMS
          </h3>

          {req.draft_insured && (
            <DraftCard
              title="To Insured"
              icon="&#128100;"
              color="border-blue-500/20 bg-blue-500/5"
              subject={req.draft_insured.subject}
              body={req.draft_insured.body}
              copyLabel="Insured Email"
            />
          )}

          {req.draft_carrier && (
            <DraftCard
              title="To Carrier"
              icon="&#127970;"
              color="border-purple-500/20 bg-purple-500/5"
              subject={req.draft_carrier.subject}
              body={req.draft_carrier.body}
              copyLabel="Carrier Email"
            />
          )}

          {req.draft_ams_note && (
            <AmsNoteCard
              note={req.draft_ams_note as { summary: string; action_items: string[]; category: string }}
            />
          )}

          {/* Copy All */}
          {(req.draft_insured || req.draft_carrier || req.draft_ams_note) && (
            <div className="pt-2 border-t border-slate-800">
              <CopyButton
                text={[
                  req.draft_insured
                    ? `=== TO INSURED ===\nSubject: ${req.draft_insured.subject}\n\n${req.draft_insured.body}`
                    : '',
                  req.draft_carrier
                    ? `\n\n=== TO CARRIER ===\nSubject: ${req.draft_carrier.subject}\n\n${req.draft_carrier.body}`
                    : '',
                  req.draft_ams_note
                    ? `\n\n=== AMS NOTE ===\nCategory: ${(req.draft_ams_note as { category: string }).category}\n${(req.draft_ams_note as { summary: string }).summary}\n\nAction Items:\n${((req.draft_ams_note as { action_items: string[] }).action_items || []).map((a) => `- ${a}`).join('\n')}`
                    : '',
                ]
                  .filter(Boolean)
                  .join('')}
                label="All Drafts"
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
