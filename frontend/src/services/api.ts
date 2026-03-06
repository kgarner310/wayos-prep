const BASE_URL = (window as any).__WAYOS_API_URL__ || '';
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
  state_wc_notes?: string | null;
  state_compliance_items?: string[] | null;
  tort_environment?: string | null;
  cat_exposures?: string[] | null;
}

export interface StateListItem {
  id: number;
  state_code: string;
  state_name: string;
}

export interface StateDetail extends StateListItem {
  wc_monopolistic: boolean;
  wc_competitive: boolean;
  wc_notes: string | null;
  regulatory_notes: string | null;
  tort_environment: string | null;
  cat_exposures: string[];
  compliance_items: string[];
  market_notes: string | null;
  top_industries: string[];
}

export interface BriefResponse {
  id: number;
  brief_json: BriefJson;
  brief_text: string;
  underwriter_email_text: string;
  internal_note_text: string;
}

export interface LossRunLineEntry {
  line_of_business: string;
  policy_year?: string;
  premium?: number;
  num_claims?: number;
  total_incurred?: number;
  total_paid?: number;
  open_reserves?: number;
  large_claims?: string[];
}

export interface LossRunAnalysisResponse {
  id: number;
  account_name: string;
  total_incurred: number | null;
  total_claims: number | null;
  loss_ratio: number | null;
  analysis_json: any;
  analysis_text: string | null;
  talking_points: string | null;
}

export interface ExperienceModAnalysisResponse {
  id: number;
  account_name: string;
  current_mod: number | null;
  prior_mod: number | null;
  analysis_json: any;
  analysis_text: string | null;
  talking_points: string | null;
}

export interface AccountListItem {
  id: number;
  name: string;
  industry: string | null;
  location: string | null;
  current_mod: number | null;
  policy_expiration: string | null;
  renewal_status: string | null;
}

export interface AccountDetail extends AccountListItem {
  employee_count: number | null;
  vehicle_exposure: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  loss_run_reviews: { id: number; account_name: string; total_incurred: number | null; total_claims: number | null; loss_ratio: number | null }[];
  experience_mod_reviews: { id: number; account_name: string; current_mod: number | null; prior_mod: number | null }[];
  briefs: { id: number; brief_text: string | null }[];
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
  listStates: () => request<StateListItem[]>('/states'),
  getState: (stateCode: string) => request<StateDetail>(`/states/${stateCode}`),

  analyzeLossRuns: (data: {
    account_name: string;
    policy_period_start?: string;
    policy_period_end?: string;
    industry?: string;
    location?: string;
    line_entries: LossRunLineEntry[];
  }) =>
    request<LossRunAnalysisResponse>('/loss-runs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getLossRunReview: (id: number) => request<LossRunAnalysisResponse>(`/loss-runs/${id}`),

  analyzeExperienceMod: (data: {
    account_name: string;
    current_mod: number;
    prior_mod?: number;
    expected_losses?: number;
    actual_primary_losses?: number;
    actual_excess_losses?: number;
    total_payroll?: number;
    state_code?: string;
    effective_date?: string;
    class_code_entries?: any[];
    mod_claims?: any[];
  }) =>
    request<ExperienceModAnalysisResponse>('/experience-mod', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getExperienceModReview: (id: number) =>
    request<ExperienceModAnalysisResponse>(`/experience-mod/${id}`),

  // --- Accounts ---
  createAccount: (data: {
    name: string;
    industry?: string;
    location?: string;
    employee_count?: number;
    current_mod?: number;
    vehicle_exposure?: string;
    policy_expiration?: string;
    renewal_status?: string;
    notes?: string;
  }) =>
    request<AccountDetail>('/accounts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  listAccounts: (renewalStatus?: string) =>
    request<AccountListItem[]>(
      renewalStatus ? `/accounts?renewal_status=${renewalStatus}` : '/accounts'
    ),
  listUpcomingRenewals: () => request<AccountListItem[]>('/accounts/renewals'),
  getAccount: (id: number) => request<AccountDetail>(`/accounts/${id}`),
  updateAccount: (id: number, data: Record<string, any>) =>
    request<AccountDetail>(`/accounts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteAccount: (id: number) =>
    request<void>(`/accounts/${id}`, { method: 'DELETE' }),
  generateAccountReview: (accountId: number) =>
    request<BriefResponse>(`/accounts/${accountId}/review`, { method: 'POST' }),
};
