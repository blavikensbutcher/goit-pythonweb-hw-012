import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Response

from src.models.user import Role
from src.services.users import get_current_user_from_token
from src.types.user_types import UserTypes


class FakeRedis:
    def __init__(self, value: str | None = None):
        self.value = value
        self.get = AsyncMock(return_value=value)
        self.set = AsyncMock()


class Token:
    def __init__(self, credentials: str):
        self.credentials = credentials


def make_user(user_id: uuid.UUID, access_token: str = "access-token") -> UserTypes:
    return UserTypes(
        id=user_id,
        name="Cached User",
        email="cached@example.com",
        password="hashed-password",
        isVerified=True,
        isBanned=False,
        role=Role.USER,
        accessToken=access_token,
        refreshToken="refresh-token",
    )


@pytest.mark.asyncio
async def test_get_current_user_returns_cached_user_without_db_lookup():
    user_id = uuid.uuid4()
    token = Token("access-token")
    cached_user = make_user(user_id)
    redis = FakeRedis(cached_user.model_dump_json())

    with (
        patch("src.services.users.decode_jwt", return_value={"sub": str(user_id)}),
        patch("src.services.users.UserService.get_user_by_id", new_callable=AsyncMock) as get_user_by_id,
    ):
        response = Response()
        user = await get_current_user_from_token(
            token,
            response=response,
            db=AsyncMock(),
            redis=redis,
        )

    assert user == cached_user
    assert response.headers["X-User-Cache"] == "HIT"
    redis.get.assert_awaited_once_with(f"user:{user_id}")
    get_user_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_caches_user_after_db_lookup_on_cache_miss():
    user_id = uuid.uuid4()
    token = Token("access-token")
    db_user = make_user(user_id)
    redis = FakeRedis()

    with (
        patch("src.services.users.decode_jwt", return_value={"sub": str(user_id)}),
        patch(
            "src.services.users.UserService.get_user_by_id",
            new_callable=AsyncMock,
            return_value=db_user,
        ) as get_user_by_id,
    ):
        response = Response()
        user = await get_current_user_from_token(
            token,
            response=response,
            db=AsyncMock(),
            redis=redis,
        )

    assert user == db_user
    assert response.headers["X-User-Cache"] == "MISS"
    get_user_by_id.assert_awaited_once()
    redis.set.assert_awaited_once()
