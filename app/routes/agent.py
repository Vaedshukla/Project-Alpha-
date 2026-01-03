import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_claims, decode_token
from app.schemas.agent import HandshakeRequest, HandshakeResponse, AgentReportRequest, AgentConfigResponse
from app.services.agent_comm import authenticate_agent, get_agent_config
from app.models.browsing_history import BrowsingHistory
from app.models.device import Device
from app.utils.responses import success


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/handshake", response_model=HandshakeResponse)
async def agent_handshake(
    payload: HandshakeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Agent registers with device_id and system_info, returns auth token."""
    token = await authenticate_agent(payload.device_id, payload.system_info, db)
    if not token:
        raise HTTPException(status_code=404, detail="Device not found or inactive")
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=1440)  # 24 hours
    
    return HandshakeResponse(
        auth_token=token,
        device_id=payload.device_id,
        expires_at=expires_at
    )


@router.post("/report")
async def agent_report(
    payload: AgentReportRequest,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Accept JSON payload of logs from agent."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        claims = decode_token(token)
        device_id = claims.get("device_id") or claims.get("sub")
        if not device_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    device = await db.get(Device, uuid.UUID(device_id))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Process and store logs
    stored = []
    for log in payload.logs:
        # Extract domain from URL
        domain = str(log.url).split("//", 1)[-1].split("/", 1)[0].lower()
        
        history = BrowsingHistory(
            id=uuid.uuid4(),
            device_id=device.id,
            url=log.url,
            domain=domain,
            category=log.category or "unrestricted",
            duration_seconds=log.duration,
            timestamp=log.timestamp
        )
        db.add(history)
        stored.append({
            "url": log.url,
            "timestamp": log.timestamp.isoformat(),
            "category": log.category
        })
    
    await db.commit()
    return success("logs stored", {"count": len(stored), "logs": stored})


@router.get("/config", response_model=AgentConfigResponse)
async def agent_config(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Returns current blocklist, policy, and focus mode schedule."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.split(" ")[1]
    try:
        claims = decode_token(token)
        device_id = claims.get("device_id") or claims.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    config = await get_agent_config(device_id, db)
    return AgentConfigResponse(**config)

