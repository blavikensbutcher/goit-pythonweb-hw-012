import uuid
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.database import get_db
from src.models.user import UpdateUserModel, UserModel 
from src.services.cache import get_redis
from src.types.user_types import UserTypes
from src.utils.auth import decode_jwt

auth_scheme = HTTPBearer()
settings = Settings()
logger = logging.getLogger(__name__)

USER_CACHE_KEY_PREFIX = "user"
USER_CACHE_STATUS_HEADER = "X-User-Cache"
USER_CACHE_TTL_HEADER = "X-User-Cache-TTL"


def _user_cache_key(user_id: str) -> str:
    return f"{USER_CACHE_KEY_PREFIX}:{user_id}"


def _set_user_cache_headers(response: Response, status: str) -> None:
    response.headers[USER_CACHE_STATUS_HEADER] = status
    response.headers[USER_CACHE_TTL_HEADER] = str(settings.redis.user_cache_ttl)
    response.headers["Cache-Control"] = "no-store"


async def _get_cached_user(redis, user_id: str) -> UserTypes | None:
    """Load a user DTO from Redis cache."""
    if redis is None:
        return None

    try:
        cached_user = await redis.get(_user_cache_key(user_id))
    except Exception:
        logger.warning("Failed to read user from Redis cache", exc_info=True)
        return None

    if not cached_user:
        return None

    try:
        return UserTypes.model_validate_json(cached_user)
    except ValidationError:
        logger.warning("Invalid cached user payload; ignoring cache", exc_info=True)
        return None


async def _cache_user(redis, user: UserTypes | UserModel) -> None:
    """Persist a user DTO in Redis cache."""
    if redis is None:
        return

    user_data = UserTypes.model_validate(user)

    try:
        await redis.set(
            _user_cache_key(str(user_data.id)),
            user_data.model_dump_json(),
            ex=settings.redis.user_cache_ttl,
        )
    except Exception:
        logger.warning("Failed to write user to Redis cache", exc_info=True)


class UserService:
    """User management service exposing CRUD operations."""

    @staticmethod
    async def get_all_users(db: AsyncSession):
        """Return all users in the database."""
        stmt = select(UserModel)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> UserTypes:
        """Return a user record identified by the provided UUID string."""
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(400, "Invalid user ID format")
            
        stmt = select(UserModel).where(UserModel.id == uid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(404, "User not found")
            
        return user

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        """Return the user model matching the specified email address."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str):
        """Delete the user with the given UUID if it exists."""
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(400, "Invalid user ID format")

        stmt = select(UserModel).where(UserModel.id == uid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(404, "User not found")

        await db.delete(user)
        await db.commit()
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: str, update_data: UpdateUserModel):
        """Update user fields from the provided payload."""
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(400, "Invalid user ID format")

        stmt = select(UserModel).where(UserModel.id == uid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(404, "User not found")

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        
        return user


async def get_current_user_from_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(auth_scheme)],
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> UserTypes:
    """Resolve the current authenticated user from the bearer token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        decoded_token = decode_jwt(token.credentials)
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    if not decoded_token:
        raise credentials_exception

    user_id: str = decoded_token.get("sub")

    if user_id is None:
        raise credentials_exception

    if redis is None:
        _set_user_cache_headers(response, "BYPASS")
    else:
        _set_user_cache_headers(response, "MISS")

    cached_user = await _get_cached_user(redis, user_id)
    if cached_user and cached_user.accessToken == token.credentials:
        _set_user_cache_headers(response, "HIT")
        return cached_user
    if cached_user:
        _set_user_cache_headers(response, "STALE")

    # Якщо користувача не знайдено, get_user_by_id сам викине HTTPException(404)
    user = await UserService.get_user_by_id(db, user_id)
    user_data = UserTypes.model_validate(user)
    await _cache_user(redis, user_data)

    return user_data
