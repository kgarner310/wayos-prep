from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExperienceModReview(Base):
    __tablename__ = "experience_mod_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Core mod data
    current_mod: Mapped[float | None] = mapped_column(Float, nullable=True)
    prior_mod: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Expected losses and payroll
    expected_losses: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_primary_losses: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_excess_losses: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_payroll: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Class code detail (JSON array)
    class_code_entries: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Claims driving the mod (JSON array)
    mod_claims: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Generated analysis
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analysis_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    talking_points: Mapped[str | None] = mapped_column(Text, nullable=True)
