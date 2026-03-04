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


class BriefResponse(BaseModel):
    id: int
    brief_json: BriefJson
    brief_text: str
    underwriter_email_text: str
    internal_note_text: str

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
