"""Pydantic schemas for public web intelligence extraction."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# --- Request ---

class PublicWebIntelRequest(BaseModel):
    company_name: str = ""
    website_url: Optional[str] = None
    social_urls: list[str] = []
    raw_website_text: str = ""
    raw_social_text: str = ""
    industry: str = ""
    state: str = ""


# --- Response sub-models ---

class CompanyIdentity(BaseModel):
    company_name: str = ""
    founded_year: Optional[int] = None
    service_area: list[str] = []


# --- Response ---

class PublicWebIntelResponse(BaseModel):
    company_identity: CompanyIdentity
    operations_signals: list[str] = []
    safety_signals: list[str] = []
    scale_signals: list[str] = []
    carrier_relevant_signals: list[str] = []
    observed_public_signals: list[str] = []
    cautions: list[str] = []


# --- Live Fetch Request ---

class PublicWebIntelFetchRequest(BaseModel):
    website_url: str
    company_name: str = ""
    industry: str = ""
    state: str = ""
    max_pages: int = 3
    max_chars: int = 20_000
    fetch_timeout_seconds: int = 15


# --- Fetch Summary sub-model ---

class FetchSummary(BaseModel):
    source_url: str = ""
    fetched_urls: list[str] = []
    fetch_warnings: list[str] = []
    success: bool = False
    fetched_char_count: int = 0


# --- Live Fetch Response ---

class PublicWebIntelFetchResponse(BaseModel):
    public_web_intel: PublicWebIntelResponse
    fetch_summary: FetchSummary


# --- Account Refresh Request ---

class AccountRefreshRequest(BaseModel):
    max_pages: int = 3
    max_chars: int = 20_000
    fetch_timeout_seconds: int = 15


# --- Account Refresh Response ---

class AccountRefreshResponse(BaseModel):
    account_id: str
    artifact_saved: bool = False
    error: Optional[str] = None
    public_web_intel: Optional[PublicWebIntelResponse] = None
    fetch_summary: Optional[FetchSummary] = None
    account_updates: list[str] = []


# --- Latest Public Intel Response ---

class LatestPublicIntelResponse(BaseModel):
    artifact_id: str
    created_at: Optional[str] = None
    content: dict = {}
