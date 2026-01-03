from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.browsing_history import BrowsingHistory
from app.models.activity_log import ActivityLog
from app.models.ai_insight import AIInsight
from app.models.device import Device


async def analyze_focus_patterns(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Compute average session length and distraction frequency for a user."""
    # Get browsing history for last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Calculate average session length (duration_seconds)
    from uuid import UUID
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    result = await db.execute(
        select(func.avg(BrowsingHistory.duration_seconds))
        .where(BrowsingHistory.device_id.in_(
            select(Device.id).where(Device.user_id == user_uuid)
        ))
        .where(BrowsingHistory.timestamp >= week_ago)
        .where(BrowsingHistory.duration_seconds.isnot(None))
    )
    avg_duration = result.scalar() or 0
    avg_session_length_minutes = avg_duration / 60.0
    
    # Count distractions (Category B/C events)
    distraction_result = await db.execute(
        select(func.count())
        .select_from(ActivityLog)
        .where(ActivityLog.user_id == user_uuid)
        .where(ActivityLog.action_type.in_(["alert_sent", "blocked"]))
        .where(ActivityLog.timestamp >= week_ago)
    )
    distraction_count = distraction_result.scalar() or 0
    hours_tracked = 7 * 24  # 7 days
    distractions_per_hour = distraction_count / hours_tracked if hours_tracked > 0 else 0
    
    return {
        "avg_session_length_minutes": float(avg_session_length_minutes),
        "distractions_per_hour": float(distractions_per_hour),
        "distraction_count": int(distraction_count)
    }


async def generate_focus_score(user_id: str, db: AsyncSession) -> float:
    """
    Generate a focus score (0-100) based on user behavior.
    Higher score = better focus.
    """
    patterns = await analyze_focus_patterns(user_id, db)
    
    avg_session = patterns["avg_session_length_minutes"]
    distractions_per_hour = patterns["distractions_per_hour"]
    
    # Score based on session length (longer = better, max at 60 minutes)
    session_score = min(avg_session / 60.0 * 50, 50)  # Max 50 points
    
    # Score based on distractions (fewer = better)
    # 0 distractions/hour = 50 points, 5+/hour = 0 points
    distraction_score = max(0, 50 - (distractions_per_hour * 10))
    
    total_score = session_score + distraction_score
    return min(100.0, max(0.0, total_score))


async def predict_distraction(user_id: str, current_time: datetime, db: AsyncSession) -> Dict[str, Any]:
    """
    Predict likely distraction risk for a user at a given time.
    Returns risk level and prediction timestamp.
    """
    patterns = await analyze_focus_patterns(user_id, db)
    distractions_per_hour = patterns["distractions_per_hour"]
    
    # Simple prediction: higher distraction rate = higher risk
    # Time-based: higher risk during typical distraction hours (afternoon)
    hour = current_time.hour
    time_factor = 1.2 if 14 <= hour <= 18 else 1.0  # Afternoon peak
    
    risk_score = distractions_per_hour * time_factor
    
    if risk_score < 0.5:
        risk_level = "low"
    elif risk_score < 2.0:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    # Predict next likely distraction time (simple: +1 hour from now if high risk)
    next_prediction = current_time + timedelta(hours=1) if risk_level == "high" else None
    
    return {
        "risk_level": risk_level,
        "risk_score": float(risk_score),
        "next_prediction": next_prediction
    }


async def update_ai_insights(user_id: str, db: AsyncSession) -> AIInsight:
    """Update or create AI insights for a user."""
    from uuid import UUID
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    patterns = await analyze_focus_patterns(user_id, db)
    focus_score = await generate_focus_score(user_id, db)
    prediction = await predict_distraction(user_id, datetime.utcnow(), db)
    
    # Get or create insight
    result = await db.execute(
        select(AIInsight).where(AIInsight.user_id == user_uuid)
    )
    insight = result.scalar_one_or_none()
    
    if insight:
        insight.focus_score = focus_score
        insight.distractions_per_hour = patterns["distractions_per_hour"]
        insight.next_prediction = prediction["next_prediction"]
        insight.avg_session_length_minutes = patterns["avg_session_length_minutes"]
        insight.updated_at = datetime.utcnow()
    else:
        insight = AIInsight(
            user_id=user_uuid,
            focus_score=focus_score,
            distractions_per_hour=patterns["distractions_per_hour"],
            next_prediction=prediction["next_prediction"],
            avg_session_length_minutes=patterns["avg_session_length_minutes"]
        )
        db.add(insight)
    
    await db.commit()
    await db.refresh(insight)
    return insight

