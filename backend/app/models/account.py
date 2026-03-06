from datetime import datetime

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(nullable=True)
    current_mod: Mapped[float | None] = mapped_column(Float, nullable=True)
    vehicle_exposure: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Renewal tracking
    policy_expiration: Mapped[str | None] = mapped_column(String(20), nullable=True)
    renewal_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # upcoming, in_progress, renewed, lost
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Links to reviews
    loss_run_reviews = relationship("LossRunReview", back_populates="account", order_by="LossRunReview.timestamp.desc()")
    experience_mod_reviews = relationship("ExperienceModReview", back_populates="account", order_by="ExperienceModReview.timestamp.desc()")
    briefs = relationship("QueryLog", back_populates="account", order_by="QueryLog.timestamp.desc()")
