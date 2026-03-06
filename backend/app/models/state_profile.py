from datetime import datetime

from sqlalchemy import String, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StateProfile(Base):
    __tablename__ = "state_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    state_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Workers comp specifics
    wc_monopolistic: Mapped[bool] = mapped_column(default=False)
    wc_competitive: Mapped[bool] = mapped_column(default=True)
    wc_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Regulatory environment
    regulatory_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tort_environment: Mapped[str | None] = mapped_column(String(50), nullable=True)  # plaintiff-friendly | moderate | tort-reform

    # Weather / catastrophe exposure
    cat_exposures: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Key compliance items
    compliance_items: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Market characteristics
    market_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Top industries in state
    top_industries: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
