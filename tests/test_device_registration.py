import types
import uuid

import pytest

from app.routes.devices import register_device
from app.schemas.device import DeviceCreate


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeDB:
    def __init__(self):
        self.added = []

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, *_args, **_kwargs):
        return FakeResult(["admin@example.com"])  # simulate admin emails


@pytest.mark.asyncio
async def test_device_registration_sends_email(monkeypatch):
    sent = {}

    def fake_send_email(subject, recipients, body, html=None, rate_key=None):
        sent["subject"] = subject
        sent["recipients"] = list(recipients)
        sent["body"] = body
        sent["rate_key"] = rate_key
        return True

    monkeypatch.setenv("PYTHONASYNCIODEBUG", "1")
    monkeypatch.setitem(register_device.__globals__, "send_email", fake_send_email)

    payload = DeviceCreate(device_name="Test Device", mac_address="AA:BB:CC", ip_address="1.2.3.4")
    claims = {"sub": str(uuid.uuid4())}
    resp = await register_device(payload, claims=claims, db=FakeDB())

    assert resp["success"] is True
    assert "Device registered" in sent["subject"]
    assert sent["recipients"] == ["admin@example.com"]

