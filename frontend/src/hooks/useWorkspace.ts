import { useState, useCallback } from 'react'
import type {
  RenewalWorkspaceResponse,
  DashboardResponse,
  EdgeScoreResponse,
  MarketSignalsResponse,
  SubmissionPacketResponse,
  SubmissionReadinessResponse,
  TimelineResponse,
} from '../api/types'
import * as api from '../api/client'

export interface WorkspaceData {
  workspace: RenewalWorkspaceResponse | null
  dashboard: DashboardResponse | null
  edgeScore: EdgeScoreResponse | null
  marketSignals: MarketSignalsResponse | null
  timeline: TimelineResponse | null
  readiness: SubmissionReadinessResponse | null
  packet: SubmissionPacketResponse | null
}

export interface UseWorkspaceReturn extends WorkspaceData {
  isLoading: boolean
  isLoadingPacket: boolean
  error: string | null
  loadWorkspace: (accountId: string, industry: string, state: string) => Promise<void>
  loadPacket: (accountId: string) => Promise<void>
}

const emptyData: WorkspaceData = {
  workspace: null,
  dashboard: null,
  edgeScore: null,
  marketSignals: null,
  timeline: null,
  readiness: null,
  packet: null,
}

export function useWorkspace(): UseWorkspaceReturn {
  const [data, setData] = useState<WorkspaceData>(emptyData)
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingPacket, setIsLoadingPacket] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadWorkspace = useCallback(async (accountId: string, industry: string, state: string) => {
    setIsLoading(true)
    setError(null)
    setData(emptyData)

    try {
      // Fire workspace + dashboard + timeline + market signals in parallel
      const [workspace, dashboard, timeline, marketSignals] = await Promise.all([
        api.generateWorkspace(accountId),
        api.getAccountDashboard(accountId).catch(() => null),
        api.getTimeline(accountId).catch(() => null),
        api.getMarketSignals(industry, state).catch(() => null),
      ])

      // Fire edge score + readiness after workspace (need workspace data)
      const [edgeScore, readiness] = await Promise.all([
        api.getEdgeScore({
          account_id: accountId,
          risk_score: workspace.risk_overview?.confidence ?? null,
          carrier_appetite: 'neutral',
        }).catch(() => null),
        api.checkSubmissionReadiness(industry).catch(() => null),
      ])

      setData({ workspace, dashboard, edgeScore, marketSignals, timeline, readiness, packet: null })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load workspace'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadPacket = useCallback(async (accountId: string) => {
    setIsLoadingPacket(true)
    try {
      const packet = await api.buildSubmissionPacket(accountId)
      setData((prev) => ({ ...prev, packet }))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to build packet'
      setError(msg)
    } finally {
      setIsLoadingPacket(false)
    }
  }, [])

  return { ...data, isLoading, isLoadingPacket, error, loadWorkspace, loadPacket }
}
