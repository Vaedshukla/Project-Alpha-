from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, UserRole
from app.services.email_service import send_email


async def send_alert(user_id: str, site: str, category: str, severity: str, db: AsyncSession) -> bool:
    """
    Send alert for Category B/C events.
    severity: "low", "medium", "high"
    category: "B" or "C"
    """
    # Get user's parent/admin emails
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return False
    
    recipients = []
    
    # Add admins
    admin_result = await db.execute(
        select(User.email).where(User.role == UserRole.admin)
    )
    recipients.extend(admin_result.scalars().all())
    
    # Add parent if user is student
    if user.role.value == "student":
        # In a real system, you'd have a parent_user_id relationship
        # For now, we'll just notify admins
        pass
    
    if not recipients:
        return False
    
    # Build alert message
    severity_emoji = {"low": "⚠️", "medium": "🔶", "high": "🔴"}.get(severity, "⚠️")
    subject = f"[Project Alpha] {severity_emoji} {category} Alert: {site}"
    
    body = f"""
Category {category} event detected:
- Site: {site}
- Severity: {severity}
- User: {user.name} ({user.email})
- Action: {'Alert sent' if category == 'B' else 'Access blocked'}
"""
    
    html = f"""
    <html>
    <body>
        <h2>{severity_emoji} Category {category} Alert</h2>
        <p><strong>Site:</strong> {site}</p>
        <p><strong>Severity:</strong> {severity}</p>
        <p><strong>User:</strong> {user.name} ({user.email})</p>
        <p><strong>Action:</strong> {'Alert sent' if category == 'B' else 'Access blocked'}</p>
    </body>
    </html>
    """
    
    rate_key = f"alert:{user_id}:{site}:{category}"
    return send_email(subject, recipients, body, html=html, rate_key=rate_key)

