import { useState, useCallback } from 'react'
import type {
  RenewalWorkspaceResponse,
  DashboardResponse,
  EdgeScoreResponse,
  SubmissionPacketResponse,
} from '../api/types'
import * as api from '../api/client'

export interface WorkspaceData {
  workspace: RenewalWorkspaceResponse | null
  dashboard: DashboardResponse | null
  edgeScore: EdgeScoreResponse | null
  packet: SubmissionPacketResponse | null
}

export interface UseWorkspaceReturn extends WorkspaceData {
  isLoading: boolean
  isLoadingPacket: boolean
  error: string | null
  loadWorkspace: (accountId: string) => Promise<void>
  loadPacket: (accountId: string) => Promise<void>
}

export function useWorkspace(): UseWorkspaceReturn {
  const [data, setData] = useState<WorkspaceData>({
    workspace: null,
    dashboard: null,
    edgeScore: null,
    packet: null,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingPacket, setIsLoadingPacket] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadWorkspace = useCallback(async (accountId: string) => {
    setIsLoading(true)
    setError(null)
    setData({ workspace: null, dashboard: null, edgeScore: null, packet: null })

    try {
      // Fire workspace + dashboard in parallel
      const [workspace, dashboard] = await Promise.all([
        api.generateWorkspace(accountId),
        api.getAccountDashboard(accountId).catch(() => null),
      ])

      // Fire edge score after we have workspace data
      let edgeScore: EdgeScoreResponse | null = null
      try {
        edgeScore = await api.getEdgeScore({
          account_id: accountId,
          risk_score: workspace.risk_overview?.confidence ?? null,
          carrier_appetite: 'neutral',
        })
      } catch {
        // non-critical
      }

      setData({ workspace, dashboard, edgeScore, packet: null })
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
