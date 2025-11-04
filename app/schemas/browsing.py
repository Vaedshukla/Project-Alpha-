from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, AnyHttpUrl


class BrowsingEvent(BaseModel):
    device_id: str
    url: AnyHttpUrl
    timestamp: datetime
    duration_seconds: int | None = None
    headers: Optional[Dict[str, Any]] = None


class BrowsingResult(BaseModel):
    category: str
    reason: str
    matched_rule: Optional[dict] = None


