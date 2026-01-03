from datetime import datetime
from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    url: str
    user_id: str


class ClassifyResponse(BaseModel):
    category: str  # "A" | "B" | "C"
    reason: str
    timestamp: datetime
    matched_pattern: str | None = None

