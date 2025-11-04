import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.responses import success
from app.core.database import get_db
from app.core.security import require_roles, Role
from app.models.blocked_site import BlockedSite, MatchType, SiteCategory
from app.schemas.blocked_site import BlockedSiteCreate, BlockedSiteUpdate


router = APIRouter(prefix="/blocked-sites", tags=["blocked-sites"])


@router.get("")
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlockedSite))
    items = [
        {
            "id": str(r.id),
            "url_pattern": r.url_pattern,
            "match_type": r.match_type.value,
            "category": r.category.value,
            "reason": r.reason,
            "is_active": r.is_active,
        }
        for r in result.scalars().all()
    ]
    return success("ok", items)


@router.post("", dependencies=[Depends(require_roles(Role.admin))])
async def add_rule(payload: BlockedSiteCreate, db: AsyncSession = Depends(get_db)):
    rule = BlockedSite(
        id=uuid.uuid4(),
        url_pattern=payload.url_pattern,
        match_type=MatchType(payload.match_type),
        category=SiteCategory(payload.category),
        reason=payload.reason,
    )
    db.add(rule)
    await db.commit()
    return success("created", {"id": str(rule.id)})


@router.put("/{rule_id}", dependencies=[Depends(require_roles(Role.admin))])
async def update_rule(rule_id: str, payload: BlockedSiteUpdate, db: AsyncSession = Depends(get_db)):
    rule = await db.get(BlockedSite, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if payload.url_pattern is not None:
        rule.url_pattern = payload.url_pattern
    if payload.match_type is not None:
        rule.match_type = MatchType(payload.match_type)
    if payload.category is not None:
        rule.category = SiteCategory(payload.category)
    if payload.reason is not None:
        rule.reason = payload.reason
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    await db.commit()
    return success("updated", {"id": str(rule.id)})


@router.delete("/{rule_id}", dependencies=[Depends(require_roles(Role.admin))])
async def deactivate_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    rule = await db.get(BlockedSite, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = False
    await db.commit()
    return success("deactivated", {"id": str(rule.id)})

