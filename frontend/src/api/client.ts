import type {
  Account,
  AuthResponse,
  DashboardResponse,
  EdgeScoreResponse,
  MarketSignalsResponse,
  RenewalWorkspaceResponse,
  SubmissionPacketResponse,
  SubmissionReadinessResponse,
  TimelineResponse,
} from './types'

const API_BASE = '/api/v1'

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function getToken(): string | null {
  return localStorage.getItem('wayos_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    let message = `Request failed: ${response.status}`
    try {
      const body = await response.json()
      message = body.detail || body.message || message
    } catch {
      // ignore parse error
    }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthResponse> {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

// ── Accounts ─────────────────────────────────────────────────────────────────

export async function listAccounts(limit = 20): Promise<{ accounts: Account[]; total: number }> {
  return request(`/accounts?limit=${limit}`)
}

export async function seedDemoAccounts(): Promise<{ accounts_created: number; accounts: Account[] }> {
  return request('/demo/seed', { method: 'POST' })
}

// ── Workspace ────────────────────────────────────────────────────────────────

export async function generateWorkspace(accountId: string): Promise<RenewalWorkspaceResponse> {
  return request(`/workspace/renewal/${accountId}`, { method: 'POST' })
}

// ── Dashboard ────────────────────────────────────────────────────────────────

export async function getAccountDashboard(accountId: string): Promise<DashboardResponse> {
  return request(`/accounts/${accountId}/dashboard`)
}

// ── Edge Score ───────────────────────────────────────────────────────────────

export async function getEdgeScore(body: Record<string, unknown>): Promise<EdgeScoreResponse> {
  return request('/edge-score', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// ── Submission Packet ────────────────────────────────────────────────────────

export async function buildSubmissionPacket(accountId: string): Promise<SubmissionPacketResponse> {
  return request(`/packet/submission/${accountId}`, { method: 'POST' })
}

// ── Public Intel Refresh ─────────────────────────────────────────────────────

export async function refreshPublicIntel(accountId: string): Promise<unknown> {
  return request(`/accounts/${accountId}/refresh-public-intel`, { method: 'POST' })
}

// ── Timeline ─────────────────────────────────────────────────────────────────

export async function getTimeline(accountId: string): Promise<TimelineResponse> {
  return request(`/accounts/${accountId}/timeline`)
}

// ── Market Signals ───────────────────────────────────────────────────────────

export async function getMarketSignals(industry?: string, state?: string): Promise<MarketSignalsResponse> {
  const params = new URLSearchParams()
  if (industry) params.set('industry', industry)
  if (state) params.set('state', state)
  const qs = params.toString()
  return request(`/market-signals${qs ? `?${qs}` : ''}`)
}

// ── Submission Readiness ─────────────────────────────────────────────────────

export async function checkSubmissionReadiness(
  industry: string,
  submissionData: Record<string, unknown> = {},
): Promise<SubmissionReadinessResponse> {
  return request('/submission/readiness', {
    method: 'POST',
    body: JSON.stringify({ industry, submission_data: submissionData }),
  })
}

// ── Demo Events ──────────────────────────────────────────────────────────────

export async function trackDemoEvent(event: string, data?: Record<string, unknown>): Promise<void> {
  try {
    await request('/demo/event', {
      method: 'POST',
      body: JSON.stringify({ event, data, timestamp: new Date().toISOString() }),
    })
  } catch {
    // non-critical
  }
}

export { ApiError }
