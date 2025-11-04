import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.responses import success
from app.core.database import get_db
from app.core.security import get_current_user_claims
from app.models.device import Device
from app.models.browsing_history import BrowsingHistory
from app.models.user import User, UserRole
from app.schemas.browsing import BrowsingEvent
from urllib.parse import urlsplit
from app.services.filter_engine import evaluate_access
from app.services.email_service import send_email


router = APIRouter(prefix="/browsing", tags=["browsing"])


@router.post("/event")
async def browsing_event(payload: BrowsingEvent, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    # Resolve device and user
    device = await db.get(Device, payload.device_id)
    if not device or str(device.user_id) != claims.get("sub"):
        raise HTTPException(status_code=404, detail="Device not found")

    # Evaluate
    evaluation = await evaluate_access(db, device, str(payload.url), {
        "timestamp": payload.timestamp.isoformat(),
        "headers": payload.headers or {},
    })

    # Persist browsing history
    netloc = urlsplit(str(payload.url)).netloc.lower()
    history = BrowsingHistory(
        id=uuid.uuid4(),
        device_id=device.id,
        url=str(payload.url),
        domain=netloc or str(payload.url),
        category='partially_restricted' if evaluation.category == 'B' else evaluation.category,
        duration_seconds=payload.duration_seconds,
        timestamp=payload.timestamp,
    )
    db.add(history)

    # Alerts for B/C
    if evaluation.category in ("B", "C"):
        admins = (await db.execute(select(User.email).where(User.role == UserRole.admin))).scalars().all()
        subject = f"Project Alpha Alert: Category {evaluation.category}"
        body = f"Device: {device.device_name}\nURL: {payload.url}\nReason: {evaluation.reason}\nMatched: {evaluation.matched_rule}"
        send_email(subject, admins, body, rate_key=f"alert:{device.id}:{str(payload.url)}")

    await db.commit()

    return success("evaluated", {
        "category": evaluation.category,
        "reason": evaluation.reason,
        "matched_rule": evaluation.matched_rule,
    })

