import { useState } from 'react'
import type { SubmissionPacketResponse } from '../../api/types'
import { copyToClipboard } from '../../lib/utils'

interface SubmissionPacketProps {
  packet: SubmissionPacketResponse
  onClose: () => void
}

export function SubmissionPacket({ packet, onClose }: SubmissionPacketProps) {
  const [copied, setCopied] = useState(false)

  const fullText = JSON.stringify(packet.packet_sections, null, 2)

  const handleCopy = async () => {
    const ok = await copyToClipboard(fullText)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Submission Packet</h3>
            <div className="flex items-center gap-2 mt-0.5">
              {packet.ready ? (
                <span className="text-[10px] text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded">Ready</span>
              ) : (
                <span className="text-[10px] text-yellow-400 bg-yellow-500/10 px-1.5 py-0.5 rounded">Incomplete</span>
              )}
              {packet.missing_items.length > 0 && (
                <span className="text-[10px] text-slate-500">
                  {packet.missing_items.length} missing item{packet.missing_items.length > 1 ? 's' : ''}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700
                         rounded transition-colors cursor-pointer"
            >
              {copied ? 'Copied!' : 'Copy All'}
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-300
                         transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>

        {/* Missing items */}
        {packet.missing_items.length > 0 && (
          <div className="px-4 py-2 bg-yellow-500/5 border-b border-slate-800">
            <div className="text-[10px] text-yellow-400 font-medium uppercase mb-1">Missing Items</div>
            {packet.missing_items.map((item, i) => (
              <div key={i} className="text-[11px] text-yellow-300/70">&#9888; {item}</div>
            ))}
          </div>
        )}

        {/* Packet content */}
        <div className="flex-1 overflow-y-auto p-4">
          {Object.entries(packet.packet_sections).map(([section, content]) => (
            <div key={section} className="mb-4">
              <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-1">
                {section.replace(/_/g, ' ')}
              </div>
              <div className="bg-slate-800/50 rounded p-3">
                <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
                  {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
