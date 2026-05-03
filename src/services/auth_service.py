import logging
import uuid
from urllib.parse import urljoin

from fastapi import HTTPException
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.constants.auth import auth_constants
from src.helpers import validate_refresh_token
from src.models.user import (
    AuthCredentials,
    CreateUserModel,
    UserModel,
)
from src.types.user_types import UserLoginResponse, UserTypes
from src.utils.auth import check_password, decode_jwt, encode_jwt, hash_password
from src.utils.mailer import Mailer

settings = Settings()
REFRESH_TOKEN_EXPIRE = settings.auth_jwt.refresh_token_expires_in
ACCESS_TOKEN_EXPIRE = settings.auth_jwt.access_token_expires_in
VERIFY_TOKEN_EXPIRE = settings.auth_jwt.verify_token_expires_in


logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user registration, login, and token management."""

    async def create_user(
        self, db: AsyncSession, user: CreateUserModel, isVerified: bool = False
    ) -> UserTypes:
        """Create a new user"""
        try:
            stmt = select(UserModel).where(UserModel.email == user.email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(409, "User already registered")

            hashed_password = hash_password(user.password)
            user_id = uuid.uuid4()

            access_payload = {
                "type": auth_constants.TOKEN_TYPE["ACCESS"],
                "sub": str(user_id),
            }
            refresh_payload = {
                "type": auth_constants.TOKEN_TYPE["REFRESH"],
                "sub": str(user_id),
            }

            access_token = encode_jwt(access_payload, expire_minutes=ACCESS_TOKEN_EXPIRE)
            refresh_token = encode_jwt(refresh_payload, expire_minutes=REFRESH_TOKEN_EXPIRE)

            new_user = UserModel(
                id=user_id,
                email=user.email,
                password=hashed_password,
                name=user.name or "",
                isVerified=isVerified,
                accessToken=access_token,
                refreshToken=refresh_token,
            )

            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            verify_token_payload = {
                "type": auth_constants.TOKEN_TYPE["VERIFY"],
                "sub": str(user_id),
            }

            verify_jwt = encode_jwt(
                verify_token_payload, expire_minutes=VERIFY_TOKEN_EXPIRE
            )

            try:
                verify_link = urljoin(settings.api.base_url, f"verify/{verify_jwt}")
                await Mailer.send_simple_message(
                    subject="Welcome!",
                    html=f"""
                        <p>Hello, {new_user.name or 'user'}!
                        Thank you for registering.</p>
                        <p>You need to verify your account by clicking on
                        <a href="{verify_link}">this link</a>.</p>
                    """,
                    sender="Gart App <no-reply@gart.com>",
                    recipient=new_user.email,
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")

            return new_user

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create user", exc_info=e)
            raise HTTPException(500, "Failed to create user")

    async def login(
        self, db: AsyncSession, credentials: AuthCredentials
    ) -> UserLoginResponse:
        """Login user and return access and refresh tokens"""
        stmt = select(UserModel).where(UserModel.email == credentials.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(404, "User not found")

        is_password_correct = check_password(credentials.password, user.password)
        if not is_password_correct:
            raise HTTPException(401, "Email or password is wrong")

        access_payload = {
            "type": auth_constants.TOKEN_TYPE["ACCESS"],
            "sub": str(user.id),
        }
        refresh_payload = {
            "type": auth_constants.TOKEN_TYPE["REFRESH"],
            "sub": str(user.id),
        }

        access_token = encode_jwt(access_payload, expire_minutes=ACCESS_TOKEN_EXPIRE)
        refresh_token = encode_jwt(refresh_payload, expire_minutes=REFRESH_TOKEN_EXPIRE)

        user.accessToken = access_token
        user.refreshToken = refresh_token

        await db.commit()
        await db.refresh(user)

        return UserLoginResponse(
            type="Bearer",
            accessToken=user.accessToken,
            refreshToken=user.refreshToken,
        )

    async def update_access_token(self, db: AsyncSession, refresh_token: str) -> str:
        """Update access token using refresh token"""
        try:
            if not await validate_refresh_token(refresh_token):
                raise HTTPException(400, "Token invalid")

            decoded_token = decode_jwt(refresh_token)
            user_id_str = decoded_token.get("sub")
            if not user_id_str:
                raise HTTPException(400, "Invalid token")

            # Parse UUID string safely
            user_id = uuid.UUID(user_id_str)

            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(404, "User not found")

        except InvalidTokenError:
            raise HTTPException(400, "Can't update access token")
        except ValueError:
            raise HTTPException(400, "Invalid user ID format in token")

        access_payload = {
            "type": auth_constants.TOKEN_TYPE["ACCESS"],
            "sub": str(user.id),
        }
        access_token = encode_jwt(access_payload, expire_minutes=ACCESS_TOKEN_EXPIRE)

        user.accessToken = access_token
        user.refreshToken = refresh_token

        await db.commit()
        await db.refresh(user)

        return access_token

    async def verify_email(self, db: AsyncSession, token: str) -> None:
        """Verify user's email address"""
        try:
            decoded_token = decode_jwt(token)
            user_id_str = decoded_token.get("sub")
            if not user_id_str:
                raise HTTPException(400, "Invalid token")

            user_id = uuid.UUID(user_id_str)

            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(404, "User not found")

            user.isVerified = True
            await db.commit()

        except HTTPException:
            raise
        except ValueError:
            raise HTTPException(400, "Invalid user ID format in token")
        except Exception as e:
            logger.error(f"Failed to verify email: {e}")
            raise HTTPException(400, "Invalid token")
    
    async def request_password_reset(self, db: AsyncSession, email: str) -> None:
        """Generate a password reset token and send it via email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # We don't raise 404 here to prevent email enumeration attacks
            return

        # Create a token specifically for password reset
        reset_payload = {
            "type": "RESET_PASSWORD",
            "sub": str(user.id),
        }
        
        # Reset token is usually short-lived (e.g., 15-30 minutes)
        reset_token = encode_jwt(reset_payload, expire_minutes=15)
        
        try:
            # Generate link to frontend app password reset page
            reset_link = urljoin(settings.api.base_url, f"reset-password?token={reset_token}")
            
            await Mailer.send_simple_message(
                subject="Password Reset Request",
                html=f"""
                    <p>Hello, {user.name or 'User'}!</p>
                    <p>You recently requested to reset your password for your account.</p>
                    <p>Click the link below to reset it. This link will expire in 15 minutes.</p>
                    <a href="{reset_link}">Reset Password</a>
                    <p>If you did not request a password reset, please ignore this email.</p>
                """,
                sender="Gart App <no-reply@gart.com>",
                recipient=user.email,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            raise HTTPException(500, "Failed to send reset email")

    async def reset_password(
        self, db: AsyncSession, token: str, new_password: str
    ) -> None:
        """Validate token and update user's password."""
        try:
            decoded_token = decode_jwt(token)
            
            if decoded_token.get("type") != "RESET_PASSWORD":
                raise HTTPException(400, "Invalid token type")
                
            user_id_str = decoded_token.get("sub")
            if not user_id_str:
                raise HTTPException(400, "Invalid token format")

            user_id = uuid.UUID(user_id_str)

            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(404, "User not found")

            # Update password
            user.password = hash_password(new_password)
            
            user.accessToken = None
            user.refreshToken = None
            
            await db.commit()

        except InvalidTokenError:
            raise HTTPException(400, "Invalid or expired reset token")
        except ValueError:
            raise HTTPException(400, "Invalid user ID format in token")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            await db.rollback()
            raise HTTPException(500, "Password reset failed")


def get_auth_service() -> AuthService:
    """Dependency for AuthService"""
    return AuthService()