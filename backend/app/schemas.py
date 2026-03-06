from datetime import datetime

from pydantic import BaseModel, Field


# --- Industry ---

class IndustryOut(BaseModel):
    id: int
    industry_name: str
    synonyms: list[str]
    top_workers_comp_claims: list[str]
    commercial_auto_claims: list[str]
    general_liability_exposures: list[str]
    conversation_prompts: list[str]
    regional_risk_notes: str | None

    model_config = {"from_attributes": True}


class IndustryListItem(BaseModel):
    id: int
    industry_name: str

    model_config = {"from_attributes": True}


# --- Brief ---

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    location: str | None = Field(default=None, max_length=200)


class PrepRequest(BaseModel):
    industry: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    employee_count: int | None = Field(default=None, ge=0, le=1_000_000)
    mod: float | None = Field(default=None, ge=0, le=10)
    vehicle_exposure: str | None = Field(default=None, max_length=200)


class BriefJson(BaseModel):
    industry: str
    location: str
    employee_count: int | None = None
    mod: float | None = None
    vehicle_exposure: str | None = None
    generated_at: str
    top_claim_drivers: list[str]
    regional_risk_notes: str
    coverage_exposures: list[str]
    conversation_starters: list[str]
    docs_to_request: list[str]
    state_wc_notes: str | None = None
    state_compliance_items: list[str] | None = None
    tort_environment: str | None = None
    cat_exposures: list[str] | None = None
    location_intel: dict | None = None


class BriefResponse(BaseModel):
    id: int
    brief_json: BriefJson
    brief_text: str
    underwriter_email_text: str
    internal_note_text: str

    model_config = {"from_attributes": True}


# --- State Profile ---

class StateProfileListItem(BaseModel):
    id: int
    state_code: str
    state_name: str

    model_config = {"from_attributes": True}


class StateProfileOut(BaseModel):
    id: int
    state_code: str
    state_name: str
    wc_monopolistic: bool
    wc_competitive: bool
    wc_notes: str | None
    regulatory_notes: str | None
    tort_environment: str | None
    cat_exposures: list[str]
    compliance_items: list[str]
    market_notes: str | None
    top_industries: list[str]

    model_config = {"from_attributes": True}


# --- Feedback ---

# --- Loss Runs ---

class LossRunLineEntry(BaseModel):
    line_of_business: str = Field(min_length=1, max_length=100)  # WC, GL, Auto, Property, Umbrella, etc.
    policy_year: str | None = Field(default=None, max_length=20)
    premium: float | None = Field(default=None, ge=0)
    num_claims: int | None = Field(default=None, ge=0)
    total_incurred: float | None = Field(default=None, ge=0)
    total_paid: float | None = Field(default=None, ge=0)
    open_reserves: float | None = Field(default=None, ge=0)
    large_claims: list[str] | None = None  # Brief descriptions of large/notable claims


class LossRunRequest(BaseModel):
    account_name: str = Field(min_length=1, max_length=255)
    policy_period_start: str | None = Field(default=None, max_length=20)
    policy_period_end: str | None = Field(default=None, max_length=20)
    industry: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    line_entries: list[LossRunLineEntry] = Field(min_length=1)


class LossRunAnalysis(BaseModel):
    id: int
    account_name: str
    total_incurred: float | None = None
    total_claims: int | None = None
    loss_ratio: float | None = None
    analysis_json: dict | None = None
    analysis_text: str | None = None
    talking_points: str | None = None

    model_config = {"from_attributes": True}


# --- Experience Mod Worksheet ---

class ClassCodeEntry(BaseModel):
    class_code: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=200)
    payroll: float | None = Field(default=None, ge=0)
    expected_loss_rate: float | None = Field(default=None, ge=0)


class ModClaim(BaseModel):
    claim_number: str | None = Field(default=None, max_length=50)
    year: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=300)
    incurred: float | None = Field(default=None, ge=0)
    medical_only: bool = False


class ExperienceModRequest(BaseModel):
    account_name: str = Field(min_length=1, max_length=255)
    state_code: str | None = Field(default=None, max_length=2)
    effective_date: str | None = Field(default=None, max_length=20)
    current_mod: float = Field(ge=0, le=10)
    prior_mod: float | None = Field(default=None, ge=0, le=10)
    expected_losses: float | None = Field(default=None, ge=0)
    actual_primary_losses: float | None = Field(default=None, ge=0)
    actual_excess_losses: float | None = Field(default=None, ge=0)
    total_payroll: float | None = Field(default=None, ge=0)
    class_code_entries: list[ClassCodeEntry] | None = None
    mod_claims: list[ModClaim] | None = None


class ExperienceModAnalysis(BaseModel):
    id: int
    account_name: str
    current_mod: float | None = None
    prior_mod: float | None = None
    analysis_json: dict | None = None
    analysis_text: str | None = None
    talking_points: str | None = None

    model_config = {"from_attributes": True}


# --- Feedback ---

class FeedbackRequest(BaseModel):
    query_log_id: int
    helpful_bool: bool
    note_text: str | None = None


class FeedbackOut(BaseModel):
    id: int
    query_log_id: int
    helpful_bool: bool
    note_text: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}
