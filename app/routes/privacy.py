from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_claims
from app.models.consent import Consent
from app.utils.responses import success


router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/summary")
async def privacy_summary(claims: dict = Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    """Show data retention and anonymization policies."""
    return success("ok", {
        "data_retention_days": 90,
        "anonymization_policy": "Browsing logs older than 90 days are anonymized (URLs removed, domains generalized)",
        "consent_required": True,
        "data_collected": [
            "Browsing history (URLs, domains, timestamps)",
            "Device information",
            "Activity logs",
            "AI insights (focus scores, distraction patterns)"
        ],
        "data_usage": [
            "Filter engine classification",
            "Focus coaching and analytics",
            "Parent/admin notifications"
        ]
    })


@router.post("/consent")
async def record_consent(claims: dict = Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    """Record consent timestamp for the current user."""
    user_id = claims.get("sub")
    
    # Get or create consent record
    result = await db.execute(
        select(Consent).where(Consent.user_id == user_id)
    )
    consent = result.scalar_one_or_none()
    
    if consent:
        if consent.consent_revoked_at:
            # Re-consent
            consent.consent_given_at = datetime.now(timezone.utc)
            consent.consent_revoked_at = None
        # If already given and not revoked, do nothing
    else:
        consent = Consent(
            user_id=user_id,
            consent_given_at=datetime.now(timezone.utc),
            version="1.0"
        )
        db.add(consent)
    
    await db.commit()
    return success("consent recorded", {
        "user_id": user_id,
        "consent_given_at": consent.consent_given_at.isoformat() if consent.consent_given_at else None,
        "version": consent.version
    })


@router.delete("/consent")
async def revoke_consent(claims: dict = Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    """Revoke consent for the current user."""
    user_id = claims.get("sub")
    
    result = await db.execute(
        select(Consent).where(Consent.user_id == user_id)
    )
    consent = result.scalar_one_or_none()
    
    if not consent:
        raise HTTPException(status_code=404, detail="No consent record found")
    
    consent.consent_revoked_at = datetime.now(timezone.utc)
    await db.commit()
    
    return success("consent revoked", {
        "user_id": user_id,
        "consent_revoked_at": consent.consent_revoked_at.isoformat()
    })

