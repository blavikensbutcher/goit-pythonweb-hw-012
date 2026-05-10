import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from fastapi import HTTPException

from src.helpers.validate_tokens import validate_access_token, validate_refresh_token


VALID_REFRESH_PAYLOAD = {
    "type": "refresh",
    "sub": "user@example.com",
    "exp": datetime.now(timezone.utc).timestamp() + 3600,
}

VALID_ACCESS_PAYLOAD = {
    "type": "access",
    "sub": "user@example.com",
    "exp": datetime.now(timezone.utc).timestamp() + 3600,
}

EXPIRED_PAYLOAD = {
    "type": "access",
    "sub": "user@example.com",
    "exp": datetime.now(timezone.utc).timestamp() - 1,
}


@pytest.mark.asyncio
async def test_validate_refresh_token_valid():
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=VALID_REFRESH_PAYLOAD):
        result = await validate_refresh_token("valid_token")
        assert result is True


@pytest.mark.asyncio
async def test_validate_refresh_token_wrong_type():
    payload = {**VALID_REFRESH_PAYLOAD, "type": "access"}
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=payload):
        with pytest.raises(HTTPException) as exc:
            await validate_refresh_token("token")
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_refresh_token_expired():
    payload = {**VALID_REFRESH_PAYLOAD, "exp": datetime.now(timezone.utc).timestamp() - 1}
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=payload):
        with pytest.raises(HTTPException) as exc:
            await validate_refresh_token("token")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_validate_refresh_token_invalid_jwt():
    from jwt import InvalidTokenError
    with patch("src.helpers.validate_tokens.decode_jwt", side_effect=InvalidTokenError):
        with pytest.raises(HTTPException) as exc:
            await validate_refresh_token("bad_token")
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_access_token_valid():
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=VALID_ACCESS_PAYLOAD):
        result = await validate_access_token("valid_token")
        assert result == VALID_ACCESS_PAYLOAD


@pytest.mark.asyncio
async def test_validate_access_token_wrong_type():
    payload = {**VALID_ACCESS_PAYLOAD, "type": "refresh"}
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=payload):
        with pytest.raises(HTTPException) as exc:
            await validate_access_token("token")
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_access_token_expired():
    with patch("src.helpers.validate_tokens.decode_jwt", return_value=EXPIRED_PAYLOAD):
        with pytest.raises(HTTPException) as exc:
            await validate_access_token("token")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_validate_access_token_invalid_jwt():
    from jwt import InvalidTokenError
    with patch("src.helpers.validate_tokens.decode_jwt", side_effect=InvalidTokenError):
        with pytest.raises(HTTPException) as exc:
            await validate_access_token("bad_token")
        assert exc.value.status_code == 400