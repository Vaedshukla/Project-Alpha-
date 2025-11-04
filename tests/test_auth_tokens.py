from app.core.security import create_access_token, decode_token


def test_access_token_contains_role():
    token = create_access_token("user-123", role="student", extra_claims={"role": "student"})
    claims = decode_token(token)
    assert claims["sub"] == "user-123"
    assert claims["type"] == "access"
    assert claims["role"] == "student"

