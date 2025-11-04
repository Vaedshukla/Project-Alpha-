from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


