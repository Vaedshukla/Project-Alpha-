from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class HandshakeRequest(BaseModel):
    device_id: str
    system_info: Dict[str, Any]
    agent_version: Optional[str] = None


class HandshakeResponse(BaseModel):
    auth_token: str
    device_id: str
    expires_at: datetime


class AgentReport(BaseModel):
    url: str
    timestamp: datetime
    category: Optional[str] = None
    duration: Optional[int] = None
    focus_mode_state: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentReportRequest(BaseModel):
    logs: list[AgentReport]


class AgentConfigResponse(BaseModel):
    blocklist: list[Dict[str, Any]]
    policy: Dict[str, Any]
    focus_mode_schedule: Optional[Dict[str, Any]] = None

