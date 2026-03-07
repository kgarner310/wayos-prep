"""Pydantic schemas for experience mod analysis request/response."""

from typing import Optional

from pydantic import BaseModel


# --- Sub-models ---

class ExperienceModClassCode(BaseModel):
    class_code: str
    description: str = ""
    payroll: float = 0.0
    expected_loss_rate: float = 0.0


class ExperienceModClaim(BaseModel):
    description: str = ""
    incurred: float = 0.0
    medical_only: bool = False
    date_of_loss: Optional[str] = None
    claim_status: str = "Closed"


# --- Request ---

class ExperienceModRequest(BaseModel):
    current_mod: float
    prior_mod: Optional[float] = None
    expected_losses: Optional[float] = None
    actual_primary_losses: Optional[float] = None
    actual_excess_losses: Optional[float] = None
    total_payroll: Optional[float] = None
    class_code_entries: list[ExperienceModClassCode] = []
    mod_claims: list[ExperienceModClaim] = []


# --- Response sub-models ---

class ExperienceModTrend(BaseModel):
    current: float
    prior: float
    change: float
    direction: str


class ExperienceModLossAnalysis(BaseModel):
    expected_losses: float
    actual_primary: float
    actual_excess: float
    actual_total: float
    deviation: float
    deviation_pct: float


class ExperienceModClaimAnalysis(BaseModel):
    description: str
    incurred: float
    medical_only: bool
    mod_impact: str
    pct_of_total: float
    date_of_loss: Optional[str] = None
    claim_status: str = "Closed"


class ExperienceModClassAnalysis(BaseModel):
    class_code: str
    description: str
    payroll: float
    expected_loss_rate: float
    expected_losses: Optional[float] = None


# --- Response ---

class ExperienceModResponse(BaseModel):
    current_mod: float
    prior_mod: Optional[float] = None
    mod_trend: Optional[ExperienceModTrend] = None
    loss_analysis: Optional[ExperienceModLossAnalysis] = None
    claims_analysis: list[ExperienceModClaimAnalysis] = []
    class_code_analysis: list[ExperienceModClassAnalysis] = []
    flags: list[str] = []
    insights: list[str] = []
    talking_points: list[str] = []
