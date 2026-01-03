import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token
from app.models.device import Device
from app.models.blocked_site import BlockedSite


async def validate_device_agent(device_id: str, shared_secret: str, signature: str, payload: str) -> bool:
    """Validate agent signature using HMAC."""
    expected = hmac.new(
        shared_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def authenticate_agent(device_id: str, system_info: Dict[str, Any], db: AsyncSession) -> Optional[str]:
    """Authenticate agent handshake and return token."""
    device = await db.get(Device, UUID(device_id))
    if not device or not device.is_active:
        return None
    
    # Create agent token (longer expiry for agents)
    token = create_access_token(
        subject=str(device.id),
        role="agent",
        extra_claims={
            "device_id": str(device.id),
            "agent": True,
            "system_info": system_info
        }
    )
    return token


async def get_agent_config(device_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Get configuration for agent (blocklist, policies, schedule)."""
    result = await db.execute(
        select(BlockedSite).where(BlockedSite.is_active == True)  # noqa: E712
    )
    rules = result.scalars().all()
    
    blocklist = [
        {
            "pattern": r.url_pattern,
            "match_type": r.match_type.value,
            "category": r.category.value,
            "reason": r.reason
        }
        for r in rules
    ]
    
    # Default policy (can be extended)
    policy = {
        "default_category": "A",
        "time_based_rules": True,
        "focus_mode_enabled": True
    }
    
    # Default focus mode schedule (9am-5pm weekdays)
    focus_schedule = {
        "enabled": True,
        "weekdays": [1, 2, 3, 4, 5],  # Monday-Friday
        "start_time": "09:00",
        "end_time": "17:00"
    }
    
    return {
        "blocklist": blocklist,
        "policy": policy,
        "focus_mode_schedule": focus_schedule
    }

