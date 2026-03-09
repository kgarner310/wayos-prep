import { useState } from 'react'
import type { NarrativeSection } from '../../api/types'
import { copyToClipboard } from '../../lib/utils'

interface NarrativePanelProps {
  narrative: NarrativeSection
}

function narrativeToString(v: string | Record<string, unknown>): string {
  if (typeof v === 'string') return v
  // Handle structured narrative objects
  if (v && typeof v === 'object') {
    if ('subject' in v && 'body' in v) {
      return `Subject: ${v.subject}\n\n${v.body}`
    }
    return JSON.stringify(v, null, 2)
  }
  return String(v)
}

export function NarrativePanel({ narrative }: NarrativePanelProps) {
  const [tab, setTab] = useState<'email' | 'memo'>('email')
  const [copied, setCopied] = useState(false)

  const emailText = narrativeToString(narrative.email_version)
  const memoText = narrativeToString(narrative.memo_version)
  const activeText = tab === 'email' ? emailText : memoText

  const handleCopy = async () => {
    const ok = await copyToClipboard(activeText)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (!emailText && !memoText) return null

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Underwriter Narrative</div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 rounded overflow-hidden">
            <button
              onClick={() => setTab('email')}
              className={`px-2.5 py-1 text-[10px] font-medium transition-colors cursor-pointer ${
                tab === 'email' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Email
            </button>
            <button
              onClick={() => setTab('memo')}
              className={`px-2.5 py-1 text-[10px] font-medium transition-colors cursor-pointer ${
                tab === 'memo' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Memo
            </button>
          </div>
          <button
            onClick={handleCopy}
            className="px-2 py-1 text-[10px] text-slate-400 hover:text-slate-200 bg-slate-800
                       hover:bg-slate-700 rounded transition-colors cursor-pointer"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 max-h-64 overflow-y-auto">
        <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{activeText}</pre>
      </div>

      {narrative.source_signals.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {narrative.source_signals.slice(0, 5).map((s, i) => (
            <span key={i} className="text-[10px] text-slate-600 bg-slate-800/50 px-1.5 py-0.5 rounded">
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
