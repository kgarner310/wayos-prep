from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LossRunReview(Base):
    __tablename__ = "loss_run_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_period_start: Mapped[str | None] = mapped_column(String(20), nullable=True)
    policy_period_end: Mapped[str | None] = mapped_column(String(20), nullable=True)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("industry_risk_profiles.id"), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # JSON array of line-level entries
    line_entries: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Generated analysis
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analysis_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    talking_points: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_incurred: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_claims: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Account link
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account", back_populates="loss_run_reviews")
