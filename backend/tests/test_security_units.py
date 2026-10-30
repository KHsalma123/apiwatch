from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, decode_access_token


def test_password_hash_and_verify():
    h = hash_password("correct horse")
    assert h != "correct horse" and h.startswith("$argon2")
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)
    assert not verify_password("x", "not-a-hash")


def test_token_roundtrip_and_tampering():
    t = create_access_token("abc123")
    assert decode_access_token(t) == "abc123"
    assert decode_access_token(t + "x") is None
    assert decode_access_token("garbage") is None
