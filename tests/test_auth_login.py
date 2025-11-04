import types

from app.routes.auth import login
from app.schemas.auth import LoginRequest
from app.models.user import User, UserRole
from app.core.security import hash_password


class FakeScalars:
    def __init__(self, item):
        self._item = item

    def one_or_none(self):
        return self._item


class FakeResult:
    def __init__(self, item):
        self._item = item

    def scalar_one_or_none(self):
        return self._item


class FakeDB:
    def __init__(self, user):
        self.user = user

    async def execute(self, *_args, **_kwargs):
        return FakeResult(self.user)


async def test_login_success():
    user = User(id=None, name="T", email="u@example.com", password_hash=hash_password("password123"), role=UserRole.student, is_active=True)
    payload = LoginRequest(email="u@example.com", password="password123")
    resp = await login(payload, db=FakeDB(user))
    assert resp["success"] is True
    assert "access_token" in resp["data"]

