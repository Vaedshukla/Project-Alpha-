from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import require_roles, Role, get_current_user_claims
from app.models.ai_insight import AIInsight
from app.models.activity_log import ActivityLog
from app.services.behavior_ai import analyze_focus_patterns, generate_focus_score
from app.utils.responses import success


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/focus/{user_id}")
async def get_focus_analytics(
    user_id: str,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """Returns focus score, top 3 distractions, improvement trend."""
    # Verify user can access this data
    if claims.get("role") != Role.admin.value and claims.get("sub") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get AI insights
    result = await db.execute(
        select(AIInsight).where(AIInsight.user_id == user_id)
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        # Generate if doesn't exist
        from app.services.behavior_ai import update_ai_insights
        insight = await update_ai_insights(user_id, db)
    
    # Get top distractions (last 10 alert/block events)
    alerts_result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .where(ActivityLog.action_type.in_(["alert_sent", "blocked"]))
        .order_by(desc(ActivityLog.timestamp))
        .limit(10)
    )
    recent_alerts = alerts_result.scalars().all()
    
    # Extract top 3 domains/URLs from alerts
    top_distractions = []
    domain_counts = {}
    for alert in recent_alerts[:10]:
        if alert.details and "url" in alert.details:
            domain = alert.details.get("url", "").split("//")[-1].split("/")[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    top_distractions = [
        {"domain": domain, "count": count}
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    ]
    
    return success("ok", {
        "focus_score": insight.focus_score,
        "distractions_per_hour": insight.distractions_per_hour,
        "avg_session_length_minutes": insight.avg_session_length_minutes,
        "top_distractions": top_distractions,
        "next_prediction": insight.next_prediction.isoformat() if insight.next_prediction else None,
        "updated_at": insight.updated_at.isoformat()
    })


@router.get("/alerts/{user_id}")
async def get_alerts_analytics(
    user_id: str,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """Returns last 10 alert events for a user."""
    if claims.get("role") != Role.admin.value and claims.get("sub") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .where(ActivityLog.action_type.in_(["alert_sent", "blocked"]))
        .order_by(desc(ActivityLog.timestamp))
        .limit(10)
    )
    alerts = result.scalars().all()
    
    alert_list = [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "details": a.details,
            "timestamp": a.timestamp.isoformat()
        }
        for a in alerts
    ]
    
    return success("ok", {
        "count": len(alert_list),
        "alerts": alert_list
    })

