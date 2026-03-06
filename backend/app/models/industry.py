from datetime import datetime

from sqlalchemy import String, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IndustryRiskProfile(Base):
    __tablename__ = "industry_risk_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    industry_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list)

    top_workers_comp_claims: Mapped[list[str]] = mapped_column(JSON, default=list)
    commercial_auto_claims: Mapped[list[str]] = mapped_column(JSON, default=list)
    general_liability_exposures: Mapped[list[str]] = mapped_column(JSON, default=list)

    conversation_prompts: Mapped[list[str]] = mapped_column(JSON, default=list)

    regional_risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
