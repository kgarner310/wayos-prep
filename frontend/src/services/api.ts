const BASE_URL = (window as any).__WAYOS_API_URL__ || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export interface IndustryListItem {
  id: number;
  industry_name: string;
}

export interface IndustryDetail extends IndustryListItem {
  synonyms: string[];
  top_workers_comp_claims: string[];
  commercial_auto_claims: string[];
  general_liability_exposures: string[];
  conversation_prompts: string[];
  regional_risk_notes: string | null;
}

export interface BriefJson {
  industry: string;
  location: string;
  employee_count: number | null;
  mod: number | null;
  vehicle_exposure: string | null;
  generated_at: string;
  top_claim_drivers: string[];
  regional_risk_notes: string;
  coverage_exposures: string[];
  conversation_starters: string[];
  docs_to_request: string[];
}

export interface BriefResponse {
  id: number;
  brief_json: BriefJson;
  brief_text: string;
  underwriter_email_text: string;
  internal_note_text: string;
}

function getApiKey(): string | null {
  return (window as any).__WAYOS_API_KEY__ || null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options?.headers as Record<string, string>) || {}),
  };

  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const res = await fetch(`${BASE_URL}${API_PREFIX}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  listIndustries: () => request<IndustryListItem[]>('/industries'),
  getIndustry: (id: number) => request<IndustryDetail>(`/industries/${id}`),
  askBrief: (question: string, location?: string) =>
    request<BriefResponse>('/briefs/ask', {
      method: 'POST',
      body: JSON.stringify({ question, location }),
    }),
  prepBrief: (data: {
    industry: string;
    location: string;
    employee_count?: number;
    mod?: number;
    vehicle_exposure?: string;
  }) =>
    request<BriefResponse>('/briefs/prep', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getBrief: (id: number) => request<BriefResponse>(`/briefs/${id}`),
  submitFeedback: (data: {
    query_log_id: number;
    helpful_bool: boolean;
    note_text?: string;
  }) =>
    request<any>('/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
