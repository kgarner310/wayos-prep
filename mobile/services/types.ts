// ── Account ──────────────────────────────────────────────────────────────────

export interface Account {
  id: string;
  account_name: string;
  named_insured: string;
  industry: string;
  state: string;
  employee_count: number | null;
  workers_comp_mod: number | null;
  current_coverages: string[];
  current_carriers: string[];
  source_type: string;
  ingestion_event_id: string | null;
  created_at: string;
  updated_at: string;
}

// ── Account Health ───────────────────────────────────────────────────────────

export interface AccountHealth {
  overall_score: number;
  coverage_score: number;
  workers_comp_score: number;
  carrier_fit_score: number;
  confidence: number;
  top_issues: string[];
  duty_to_advise_alert_count: number;
  updated_at: string;
}

// ── Artifacts ────────────────────────────────────────────────────────────────

export type ArtifactStatus = 'pending' | 'ready' | 'failed';

export interface Artifact {
  id: string;
  account_id: string;
  artifact_type: string;
  title: string;
  content_json: Record<string, any> | null;
  status: ArtifactStatus;
  confidence: number | null;
  model_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CoverageGapArtifact {
  artifact_type: 'coverage_gap';
  risk_level: string;
  gaps: string[];
  recommended_coverages: string[];
  duty_to_advise_flags: string[];
  producer_talking_points: string[];
  unknowns: string[];
}

export interface MeetingBriefArtifact {
  artifact_type: 'meeting_brief';
  client_summary: string;
  key_risks: string[];
  coverage_concerns: string[];
  questions_for_client: string[];
  conversation_strategy: string;
}

export interface WorkersCompSnapshotArtifact {
  artifact_type: 'workers_comp_snapshot';
  mod: number | null;
  industry_average_mod: number | null;
  premium_signal: string;
  risk_drivers: string[];
  improvement_opportunities: string[];
  unknowns: string[];
}

export interface WinnabilityArtifact {
  artifact_type: 'winnability';
  score: number;
  band: string;
  reasons: string[];
  talking_points: string[];
  next_actions: string[];
}

// ── Insights ─────────────────────────────────────────────────────────────────

export interface InsightItem {
  insight_type: string;
  title: string;
  subtitle: string;
  suggested_action: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
}

// ── API Responses ────────────────────────────────────────────────────────────

export interface DashboardResponse {
  account: Account;
  health: AccountHealth;
  artifacts: Artifact[];
  insights: InsightItem[];
}

export interface CaptureResponse {
  ingestion_event_id: string;
  source_type: string;
  extracted_text: string;
  signals: Record<string, any>;
}

// ── API Requests ─────────────────────────────────────────────────────────────

export interface ManualAccountCreate {
  account_name: string;
  named_insured: string;
  industry: string;
  state: string;
  employee_count?: number | null;
  workers_comp_mod?: number | null;
  current_coverages?: string[];
  current_carriers?: string[];
}

export interface AccountFromCaptureRequest {
  ingestion_event_id: string;
  account_name?: string;
  named_insured?: string;
}

export interface OutcomeCreate {
  account_id: string;
  outcome: 'won' | 'lost' | 'renewed';
  reason: string;
  carrier?: string;
  premium?: number;
  competitor?: string;
  notes?: string;
}
