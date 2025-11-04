from datetime import datetime
from pydantic import BaseModel


class DeviceCreate(BaseModel):
    device_name: str
    mac_address: str
    ip_address: str | None = None


class DeviceOut(BaseModel):
    id: str
    device_name: str
    mac_address: str
    ip_address: str | None
    registered_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


