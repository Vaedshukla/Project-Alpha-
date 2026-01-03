from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_claims
from app.schemas.filter import ClassifyRequest, ClassifyResponse
from app.services.filter_engine import classify_request
from app.utils.responses import success


router = APIRouter(prefix="/filter", tags=["filter"])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_url(
    payload: ClassifyRequest,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Classify a URL into category A (unrestricted), B (partially restricted), or C (blocked).
    Returns JSON with category, reason, timestamp.
    """
    # Verify user_id matches token
    user_id = claims.get("sub")
    if payload.user_id != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    result = await classify_request(db, payload.url, payload.user_id)
    
    return ClassifyResponse(
        category=result["category"],
        reason=result["reason"],
        timestamp=result["timestamp"],
        matched_pattern=result.get("matched_pattern")
    )

