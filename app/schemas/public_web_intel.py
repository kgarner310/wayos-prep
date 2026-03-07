"""Pydantic schemas for public web intelligence extraction."""

from typing import Optional

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
