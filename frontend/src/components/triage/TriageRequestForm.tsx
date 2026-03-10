import { useState } from 'react'
import { createTriageRequest } from '../../api/client'
import type { Account } from '../../api/types'

interface TriageRequestFormProps {
  onSubmit: () => void
  onCancel: () => void
  account?: Account
}

const INPUT_TYPES = [
  { value: 'text', label: 'Text / Email' },
  { value: 'voice_transcript', label: 'Voice Transcript' },
  { value: 'file', label: 'File (coming soon)', disabled: true },
]

const PLACEHOLDER_EXAMPLES = `Paste or type the service request here. Examples:

"Hi, I need a certificate of insurance sent to ABC General Contractors by end of day. They need us listed as additional insured on the GL policy."

"Got a voicemail from Jane at Midwest Plumbing — she said they bought a new service van, 2024 Ford Transit, VIN 1FTBW2... Need to add it to the commercial auto policy."

"Insured reported a slip-and-fall at their warehouse this morning. Employee was taken to urgent care. Need to file a WC claim with Travelers."
`

export function TriageRequestForm({ onSubmit, onCancel, account }: TriageRequestFormProps) {
  const [inputType, setInputType] = useState('text')
  const [inputText, setInputText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!inputText.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      await createTriageRequest({
        input_text: inputText.trim(),
        input_type: inputType,
        account_id: account?.id,
      })
      onSubmit()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create request')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-100">New Service Request</h2>
          <p className="text-sm text-slate-500 mt-1">
            Drop in a request and AI will triage it and draft messages
          </p>
        </div>
        <button
          onClick={onCancel}
          className="text-sm text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
        >
          Cancel
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Input type selector */}
        <div>
          <label className="block text-xs text-slate-500 mb-2">Input Type</label>
          <div className="flex gap-2">
            {INPUT_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                disabled={type.disabled}
                onClick={() => !type.disabled && setInputType(type.value)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors cursor-pointer ${
                  inputType === type.value
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : type.disabled
                    ? 'text-slate-700 cursor-not-allowed'
                    : 'text-slate-500 hover:text-slate-300 border border-slate-800 hover:border-slate-700'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Text input */}
        <div>
          <label className="block text-xs text-slate-500 mb-2">
            {inputType === 'voice_transcript' ? 'Voice Transcript' : 'Request Details'}
          </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={PLACEHOLDER_EXAMPLES}
            rows={10}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 resize-none"
            autoFocus
          />
          <p className="text-[10px] text-slate-700 mt-1">
            Paste an email, voicemail transcript, or type the request. AI handles the rest.
          </p>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || !inputText.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
          >
            {submitting ? 'Triaging...' : 'Triage Request'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2.5 text-sm text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
