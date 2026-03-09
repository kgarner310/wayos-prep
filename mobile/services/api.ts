import {
  Account,
  AccountHealth,
  Artifact,
  DashboardResponse,
  CaptureResponse,
  InsightItem,
  ManualAccountCreate,
  AccountFromCaptureRequest,
  OutcomeCreate,
} from './types';

const API_BASE =
  process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore parse error
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

async function requestMultipart<T>(
  path: string,
  formData: FormData
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    // Let browser set Content-Type with boundary for multipart
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore parse error
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

// ── Account Search ───────────────────────────────────────────────────────────

export async function searchAccounts(
  q: string
): Promise<{ accounts: Account[]; total: number }> {
  return request(`/accounts/search?q=${encodeURIComponent(q)}`);
}

// ── Account Dashboard ────────────────────────────────────────────────────────

export async function getAccountDashboard(
  accountId: string
): Promise<DashboardResponse> {
  return request(`/accounts/${accountId}/dashboard`);
}

// ── Create Manual Account ────────────────────────────────────────────────────

export async function createManualAccount(
  data: ManualAccountCreate
): Promise<{ account: Account; health: AccountHealth }> {
  return request('/accounts/manual', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Capture File ─────────────────────────────────────────────────────────────

export async function captureFile(file: any): Promise<CaptureResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return requestMultipart('/capture/upload', formData);
}

// ── Account From Capture ─────────────────────────────────────────────────────

export async function accountFromCapture(
  data: AccountFromCaptureRequest
): Promise<{ account: Account; health: AccountHealth }> {
  return request('/capture/create-account', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Generate Artifacts ───────────────────────────────────────────────────────

export async function generateArtifacts(
  accountId: string,
  artifactType?: string
): Promise<{ status: string }> {
  const params = artifactType
    ? `?artifact_type=${encodeURIComponent(artifactType)}`
    : '';
  return request(`/accounts/${accountId}/artifacts/generate${params}`, {
    method: 'POST',
  });
}

// ── Account Insights ─────────────────────────────────────────────────────────

export async function getAccountInsights(
  accountId: string
): Promise<{ insights: InsightItem[] }> {
  return request(`/accounts/${accountId}/insights`);
}

// ── Submit Outcome ───────────────────────────────────────────────────────────

export async function submitOutcome(
  data: OutcomeCreate
): Promise<{ status: string }> {
  return request('/outcomes', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── List Accounts ────────────────────────────────────────────────────────────

export async function listAccounts(
  limit: number = 20
): Promise<{ accounts: Account[]; total: number }> {
  return request(`/accounts?limit=${limit}`);
}
