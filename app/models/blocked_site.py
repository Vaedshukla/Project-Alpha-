import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MatchType(str, Enum):
    exact = "exact"
    domain = "domain"
    regex = "regex"


class SiteCategory(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class BlockedSite(Base):
    __tablename__ = "blocked_sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_pattern: Mapped[str] = mapped_column(String(1024), nullable=False)
    match_type: Mapped[MatchType] = mapped_column(SAEnum(MatchType, name="match_type"), nullable=False)
    category: Mapped[SiteCategory] = mapped_column(SAEnum(SiteCategory, name="site_category"), nullable=False)
    reason: Mapped[str] = mapped_column(String(512), nullable=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

