import re
import socket
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blocked_site import BlockedSite, MatchType, SiteCategory
from app.models.device import Device
from app.models.activity_log import ActivityLog
from app.models.admin_action import AdminAction
from app.models.browsing_history import BrowsingHistory
from app.services.email_service import send_email


@dataclass
class EvaluationResult:
    category: str
    reason: str
    matched_rule: Optional[Dict[str, Any]]


def _extract_domain(url: str) -> str:
    try:
        # naive extraction; rely on urlparse in future if needed
        host = url.split("//", 1)[-1].split("/", 1)[0]
        return host.lower()
    except Exception:
        return url


def _match_rule(url: str, domain: str, rule: BlockedSite) -> bool:
    pattern = rule.url_pattern
    if rule.match_type == MatchType.exact:
        return url.lower() == pattern.lower()
    if rule.match_type == MatchType.domain:
        return domain.endswith(pattern.lower())
    if rule.match_type == MatchType.regex:
        try:
            return re.search(pattern, url, flags=re.IGNORECASE) is not None
        except re.error:
            return False
    return False


async def _find_matching_rule(db: AsyncSession, url: str, domain: str) -> Optional[BlockedSite]:
    result = await db.execute(select(BlockedSite).where(BlockedSite.is_active == True))  # noqa: E712
    for rule in result.scalars().all():
        if _match_rule(url, domain, rule):
            return rule
    return None


def _within_block_hours(now: datetime) -> bool:
    # Example policy: block social media 09:00-17:00 local
    start = time(9, 0)
    end = time(17, 0)
    return start <= now.time() <= end


async def evaluate_access(db: AsyncSession, device: Device, url: str, metadata: Dict[str, Any]) -> EvaluationResult:
    domain = _extract_domain(url)

    # Confidence/category mapping via blocked_sites
    matched = await _find_matching_rule(db, url, domain)
    if matched:
        mapping = matched.category.value
        reason = matched.reason or f"Matched rule {matched.id}"
        if mapping in (SiteCategory.B.value, SiteCategory.C.value):
            return EvaluationResult(category=mapping, reason=reason, matched_rule={
                "id": str(matched.id),
                "pattern": matched.url_pattern,
                "type": matched.match_type.value,
            })

    # Time-based example: block social media domains during work/school hours → Category B alert
    if _within_block_hours(datetime.utcnow()) and any(k in domain for k in ["facebook.com", "instagram.com", "tiktok.com", "x.com", "twitter.com"]):
        return EvaluationResult(category="B", reason="Time-based policy window", matched_rule=None)

    # Default Category A
    return EvaluationResult(category="A", reason="No matching restrictions", matched_rule=None)


async def enforce_action(db: AsyncSession, evaluation: EvaluationResult, device: Device, user_id: Optional[str], url: Optional[str] = None, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
    # Persist browsing history entry
    domain = _extract_domain(evaluation.matched_rule.get("pattern") if evaluation.matched_rule else "")

    # No URL provided here; caller should have already created browsing history with real URL.
    # We only handle activity logs and admin actions plus return directive.
    if evaluation.category == "A":
        await db.merge(ActivityLog(action_type="visit", user_id=user_id, device_id=device.id, details={"category": "A"}))
        await db.flush()
        return {"allowed": True}

    if evaluation.category == "B":
        await db.merge(ActivityLog(action_type="alert_sent", user_id=user_id, device_id=device.id, details={"reason": evaluation.reason}))
        # Notify admins for MVP
        from app.models.user import User, UserRole
        admins = (await db.execute(select(User.email).where(User.role == UserRole.admin))).scalars().all()
        subj = "[Project Alpha] Category B access detected"
        body = f"Device {device.device_name} attempted access to {url} at {timestamp or datetime.utcnow().isoformat()} - Reason: {evaluation.reason}"
        send_email(subj, admins, body, rate_key=f"B:{device.id}:{evaluation.matched_rule.get('id') if evaluation.matched_rule else url}")
        await db.flush()
        return {"allowed": True, "alert": True}

    if evaluation.category == "C":
        await db.merge(ActivityLog(action_type="blocked", user_id=user_id, device_id=device.id, details={"reason": evaluation.reason}))
        from app.models.user import User, UserRole
        admin_obj = (await db.execute(select(User).where(User.role == UserRole.admin))).scalars().first()
        admin_id = admin_obj.id if admin_obj else None
        if admin_id is not None:
            await db.merge(AdminAction(admin_id=admin_id, action="auto_block", target_type="site", target_id=None, notes=evaluation.reason))
        admins = (await db.execute(select(User.email).where(User.role == UserRole.admin))).scalars().all()
        subj = "[Project Alpha] Category C attempt blocked"
        body = f"Device {device.device_name} was blocked from accessing {url} at {timestamp or datetime.utcnow().isoformat()} - Reason: {evaluation.reason}"
        send_email(subj, admins, body, rate_key=f"C:{device.id}:{evaluation.matched_rule.get('id') if evaluation.matched_rule else url}")
        await db.flush()
        return {"allowed": False}

    return {"allowed": True}

