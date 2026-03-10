// ── Account ──────────────────────────────────────────────────────────────────

export interface Account {
  id: string
  account_name: string
  named_insured: string
  industry: string
  state: string
  employee_count: number | null
  workers_comp_mod: number | null
  current_coverages: string[]
  current_carriers: string[]
  source_type: string
  ingestion_event_id: string | null
  created_at: string
  updated_at: string
}

// ── Account Health ───────────────────────────────────────────────────────────

export interface AccountHealth {
  overall_score: number
  coverage_score: number
  workers_comp_score: number
  carrier_fit_score: number
  confidence: number
  top_issues: string[]
  duty_to_advise_alert_count: number
  updated_at: string
}

// ── Artifacts ────────────────────────────────────────────────────────────────

export type ArtifactStatus = 'pending' | 'ready' | 'failed'

export interface Artifact {
  id: string
  account_id: string
  artifact_type: string
  title: string
  content_json: Record<string, unknown> | null
  status: ArtifactStatus
  confidence: number | null
  model_name: string | null
  created_at: string
  updated_at: string
}

// ── Market Edge ──────────────────────────────────────────────────────────────

export interface CarrierWinRate {
  carrier: string
  win_rate: number
  wins: number
  losses: number
}

export interface LossReason {
  reason: string
  count: number
}

export interface MarketEdge {
  industry: string
  state: string
  sample_size: number
  carrier_win_rates: CarrierWinRate[]
  top_loss_reasons: LossReason[]
  confidence: 'low' | 'normal'
}

// ── Insights ─────────────────────────────────────────────────────────────────

export interface InsightItem {
  insight_type: string
  title: string
  subtitle: string
  suggested_action: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
}

// ── Memory ───────────────────────────────────────────────────────────────────

export interface MemoryEntry {
  id: string
  account_id: string
  entry_type: string
  summary: string
  payload_json: Record<string, unknown> | null
  created_by: string | null
  created_at: string
}

// ── Dashboard Response ───────────────────────────────────────────────────────

export interface DashboardResponse {
  account: Account
  health: AccountHealth
  artifacts: Artifact[]
  insights: InsightItem[]
  memory: MemoryEntry[]
  market_edge: MarketEdge
}

// ── Renewal Workspace ────────────────────────────────────────────────────────

export interface CompanyIdentitySummary {
  company_name: string
  founded_year: number | null
  service_area: string[]
}

export interface OperationsSignals {
  company_identity: CompanyIdentitySummary
  operations_signals: string[]
  safety_signals: string[]
  scale_signals: string[]
  carrier_relevant_signals: string[]
}

export interface AccountSummary {
  account_name: string
  industry: string
  state: string
  account_stage: string
  key_facts: string[]
}

export interface RiskOverview {
  risk_level: string
  confidence: number
  headline: string
  contributing_factors: string[]
  signal_count: number
}

export interface AppliedRule {
  code: string
  description: string
  confidence_delta: number
}

export interface CoverageGap {
  coverage: string
  reason: string
  risk_level: string
  confidence: number
  applied_rules: AppliedRule[]
  why_this_is_here: string[]
}

export interface NarrativeSection {
  email_version: string | Record<string, unknown>
  memo_version: string | Record<string, unknown>
  style_applied: Record<string, unknown>
  fact_sources: Record<string, unknown>
  source_signals: string[]
}

export interface RenewalWorkspaceResponse {
  account_id: string
  account_summary: AccountSummary
  operations_signals: OperationsSignals
  risk_overview: RiskOverview
  coverage_gaps: CoverageGap[]
  producer_questions: string[]
  underwriter_narrative: NarrativeSection
  recommended_actions: string[]
  sections_available: string[]
  error: string | null
}

// ── Edge Score ───────────────────────────────────────────────────────────────

export interface EdgeScoreResponse {
  overall_score: number
  band: string
  drivers: string[]
  drags: string[]
  summary: string
}

// ── Submission Packet ────────────────────────────────────────────────────────

export interface SubmissionPacketResponse {
  account_id: string
  packet_sections: Record<string, unknown>
  ready: boolean
  missing_items: string[]
  generated_at: string
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
  email: string
}

export interface User {
  user_id: string
  email: string
}

// ── Timeline ─────────────────────────────────────────────────────────────────

export interface TimelineEvent {
  id: string
  event_type: string
  notes: string | null
  created_at: string | null
}

export interface TimelineResponse {
  account_id: string
  events: TimelineEvent[]
  count: number
}

// ── Market Signals ───────────────────────────────────────────────────────────

export interface MarketSignalsResponse {
  carrier_win_rates: Record<string, number>
  loss_reasons: Record<string, number>
  total_outcomes: number
  win_rate_overall: number
  top_carrier: string | null
}

// ── Service Triage ──────────────────────────────────────────────────────────

export type TriageStatus = 'pending' | 'triaged' | 'approved' | 'rejected'
export type TriageUrgency = 'urgent' | 'high' | 'medium' | 'low'

export interface DraftMessage {
  subject: string
  body: string
}

export interface DraftAmsNote {
  summary: string
  action_items: string[]
  category: string
}

export interface TriageRequest {
  id: string
  account_id: string | null
  agency_id: string | null
  created_by_user_id: string | null
  input_type: string
  input_text: string
  input_filename: string | null
  input_extracted_text: string | null
  status: TriageStatus
  request_type: string | null
  urgency: TriageUrgency | null
  summary: string | null
  draft_insured: DraftMessage | null
  draft_carrier: DraftMessage | null
  draft_ams_note: DraftAmsNote | null
  approved_at: string | null
  approved_by_user_id: string | null
  confidence: number | null
  model_name: string | null
  created_at: string
  updated_at: string
}

export interface TriageListResponse {
  requests: TriageRequest[]
  total: number
}

// ── PIT Dispatch ─────────────────────────────────────────────────────────────

export interface DispatchRecord {
  id: string
  triage_request_id: string | null
  account_id: string | null
  agency_id: string | null
  recipient_type: string
  channel: string
  subject: string | null
  body: string
  dispatched_by_user_id: string | null
  dispatched_at: string
  status: string
  created_at: string
}

export interface DispatchListResponse {
  dispatches: DispatchRecord[]
  total: number
}

export interface PITFeedItem {
  item_type: 'triage' | 'dispatch'
  item_id: string
  timestamp: string
  summary: string
  urgency: string | null
  status: string
  recipient_type: string | null
  request_type: string | null
}

export interface PITFeedResponse {
  items: PITFeedItem[]
  total: number
}

export interface PITStats {
  pending_triage: number
  urgent_count: number
  dispatches_today: number
  accounts_touched: number
}

// ── Submission Readiness ─────────────────────────────────────────────────────

export interface SubmissionReadinessResponse {
  industry: string
  jurisdiction: string
  readiness_score: number
  readiness_level: 'strong' | 'good' | 'fair' | 'poor'
  missing_critical_fields: string[]
  missing_recommended_fields: string[]
  weak_fields: string[]
  strengths: string[]
  next_steps: string[]
  explanation: string
}
