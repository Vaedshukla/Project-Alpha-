from pydantic import BaseModel


class BlockedSiteCreate(BaseModel):
    url_pattern: str
    match_type: str
    category: str
    reason: str | None = None


class BlockedSiteUpdate(BaseModel):
    url_pattern: str | None = None
    match_type: str | None = None
    category: str | None = None
    reason: str | None = None
    is_active: bool | None = None


