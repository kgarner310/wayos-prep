from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    query_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ask | prep | lookup

    raw_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("industry_risk_profiles.id"), nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mod: Mapped[float | None] = mapped_column(Float, nullable=True)
    vehicle_exposure: Mapped[str | None] = mapped_column(String(255), nullable=True)

    brief_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    brief_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    underwriter_email_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_note_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    llm_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
