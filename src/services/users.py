import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import UpdateUserModel, UserModel 
from src.types.user_types import UserTypes
from src.utils.auth import decode_jwt

auth_scheme = HTTPBearer()


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
    db: AsyncSession = Depends(get_db),
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
        
    # Якщо користувача не знайдено, get_user_by_id сам викине HTTPException(404)
    user = await UserService.get_user_by_id(db, user_id)

    return user