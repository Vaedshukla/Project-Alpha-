import asyncio
from types import SimpleNamespace

import pytest

from app.models.blocked_site import BlockedSite, MatchType, SiteCategory
from app.models.device import Device
from app.services.filter_engine import evaluate_access


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return SimpleNamespace(all=lambda: self._items)


class FakeSession:
    def __init__(self, rules):
        self.rules = rules

    async def execute(self, *_args, **_kwargs):
        return FakeResult(self.rules)


@pytest.mark.asyncio
async def test_filter_exact_block_category_c():
    rule = BlockedSite(id=None, url_pattern="http://bad.com/x", match_type=MatchType.exact, category=SiteCategory.C, reason="test", added_by=None, is_active=True)
    device = Device(id=None, user_id=None, device_name="d1", mac_address="m", ip_address=None, is_active=True)
    res = await evaluate_access(FakeSession([rule]), device, "http://bad.com/x", {})
    assert res.category == "C"


@pytest.mark.asyncio
async def test_filter_domain_alert_category_b():
    rule = BlockedSite(id=None, url_pattern="facebook.com", match_type=MatchType.domain, category=SiteCategory.B, reason="test", added_by=None, is_active=True)
    device = Device(id=None, user_id=None, device_name="d1", mac_address="m", ip_address=None, is_active=True)
    res = await evaluate_access(FakeSession([rule]), device, "http://facebook.com/page", {})
    assert res.category == "B"


@pytest.mark.asyncio
async def test_filter_default_category_a():
    device = Device(id=None, user_id=None, device_name="d1", mac_address="m", ip_address=None, is_active=True)
    res = await evaluate_access(FakeSession([]), device, "http://edu.example.com", {})
    assert res.category == "A"

