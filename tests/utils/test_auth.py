import pytest
from src.utils.auth import hash_password, check_password, encode_jwt, decode_jwt


class TestAuthUtils:
    def test_hash_password(self):
        password = "testpassword"
        hashed = hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)

    def test_check_password(self):
        password = "testpassword"
        hashed = hash_password(password)
        assert check_password(password, hashed) is True
        assert check_password("wrongpassword", hashed) is False

    def test_encode_decode_jwt(self):
        payload = {"sub": "123", "type": "access"}
        token = encode_jwt(payload, expire_minutes=1)
        decoded = decode_jwt(token)
        assert decoded["sub"] == "123"
        assert decoded["type"] == "access"