from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    query_log_id: Mapped[int] = mapped_column(ForeignKey("query_logs.id"), nullable=False)
    helpful_bool: Mapped[bool] = mapped_column(Boolean, nullable=False)
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)
