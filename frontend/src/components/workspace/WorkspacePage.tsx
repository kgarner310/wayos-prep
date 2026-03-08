import { useEffect, useState } from 'react'
import type { Account } from '../../api/types'
import { useWorkspace } from '../../hooks/useWorkspace'
import * as api from '../../api/client'
import { AccountHeader } from './AccountHeader'
import { HealthScoreCard } from './HealthScoreCard'
import { RiskOverviewCard } from './RiskOverviewCard'
import { EdgeScoreCard } from './EdgeScoreCard'
import { CoverageGapsPanel } from './CoverageGapsPanel'
import { OperationsSignalsPanel } from './OperationsSignalsPanel'
import { NarrativePanel } from './NarrativePanel'
import { ProducerQuestionsCard } from './ProducerQuestionsCard'
import { RecommendedActions } from './RecommendedActions'
import { SubmissionPacket } from './SubmissionPacket'

interface WorkspacePageProps {
  account: Account
}

export function WorkspacePage({ account }: WorkspacePageProps) {
  const {
    workspace,
    dashboard,
    edgeScore,
    packet,
    isLoading,
    isLoadingPacket,
    error,
    loadWorkspace,
    loadPacket,
  } = useWorkspace()

  const [showPacket, setShowPacket] = useState(false)

  useEffect(() => {
    loadWorkspace(account.id)
    api.trackDemoEvent('workspace_opened', { account_id: account.id })
  }, [account.id, loadWorkspace])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mb-3" />
          <div className="text-sm text-slate-400">Generating intelligence...</div>
          <div className="text-[11px] text-slate-600 mt-1">Analyzing {account.account_name}</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-sm">
          <div className="text-sm text-red-400 mb-2">Error loading workspace</div>
          <div className="text-xs text-slate-500 mb-4">{error}</div>
          <button
            onClick={() => loadWorkspace(account.id)}
            className="px-4 py-2 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!workspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-sm text-slate-500">Select an account to begin</div>
      </div>
    )
  }

  const handleBuildPacket = async () => {
    await loadPacket(account.id)
    setShowPacket(true)
    api.trackDemoEvent('packet_built', { account_id: account.id })
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Account header */}
      <AccountHeader summary={workspace.account_summary} />

      {/* Score cards row */}
      <div className="grid grid-cols-3 gap-3">
        {dashboard?.health ? (
          <HealthScoreCard health={dashboard.health} />
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Account Health</div>
            <div className="text-xs text-slate-600">Not available</div>
          </div>
        )}

        <RiskOverviewCard risk={workspace.risk_overview} />

        {edgeScore ? (
          <EdgeScoreCard edge={edgeScore} />
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-3">Competitive Edge</div>
            <div className="text-xs text-slate-600">Not available</div>
          </div>
        )}
      </div>

      {/* Two-column: Coverage Gaps + Operations Signals */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <CoverageGapsPanel gaps={workspace.coverage_gaps} />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <OperationsSignalsPanel signals={workspace.operations_signals} />
        </div>
      </div>

      {/* Narrative */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <NarrativePanel narrative={workspace.underwriter_narrative} />
      </div>

      {/* Two-column: Questions + Actions */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <ProducerQuestionsCard questions={workspace.producer_questions} />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <RecommendedActions actions={workspace.recommended_actions} />
        </div>
      </div>

      {/* Submission packet button */}
      <div className="flex justify-center pb-4">
        <button
          onClick={handleBuildPacket}
          disabled={isLoadingPacket}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500
                     text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
        >
          {isLoadingPacket ? 'Building Packet...' : 'Build Submission Packet'}
        </button>
      </div>

      {/* Packet modal */}
      {showPacket && packet && (
        <SubmissionPacket packet={packet} onClose={() => setShowPacket(false)} />
      )}
    </div>
  )
}
