import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    distractions_per_hour: Mapped[float] = mapped_column(Float, nullable=False)
    next_prediction: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avg_session_length_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

