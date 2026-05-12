from typing import Annotated


from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.limiter import limiter 


from src.database import get_db
from src.helpers.validate_tokens import validate_access_token
from src.models.user import (
    AuthCredentials,
    CreateUserModel,
    PasswordResetConfirmModel,
    PasswordResetRequestModel,
)
from src.services.auth_service import AuthService, get_auth_service
from src.services.users import (
    UserService,
    get_current_user_from_token,
)
from src.types.user_types import (
    CurrentUserDto,
    UserAccessTokenUpdate,
    UserAccessTokenUpdateResponse,
    UserLoginResponse,
    UserTypes,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


def get_user_service() -> UserService:
    """Dependency for UserService"""
    return UserService()


@router.post(
    "/signup",
    response_model=UserLoginResponse,
    status_code=201,
    responses={201: {"description": "Successfully registered"}},
)
async def sign_up(
    user: CreateUserModel,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponse:
    """Create a new user"""
    created_user = await auth_service.create_user(db, user)
    return UserLoginResponse(
        type="Bearer",
        accessToken=created_user.accessToken,
        refreshToken=created_user.refreshToken,
    )


@router.post(
    "/signin",
    response_model=UserLoginResponse,
    status_code=200,
    responses={200: {"description": "Successfully signed in"}},
)
async def sign_in(
    user: AuthCredentials,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponse:
    """Sign in an existing user"""
    auth_user = await auth_service.login(db, user)
    return UserLoginResponse(
        type="Bearer",
        accessToken=auth_user.accessToken,
        refreshToken=auth_user.refreshToken,
    )


@router.post(
    "/refresh-token",
    response_model=UserAccessTokenUpdateResponse,
    status_code=200,
    responses={200: {"description": "Token successfully updated"}},
)
async def refresh(
    refreshTokenUpdateDto: UserAccessTokenUpdate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserAccessTokenUpdateResponse:
    """Update access token using refresh token"""
    try:
        access_token = await auth_service.update_access_token(
            db, refreshTokenUpdateDto.refreshToken
        )
        return UserAccessTokenUpdateResponse(
            type="Bearer",
            accessToken=access_token,
        )
    except Exception:
        raise HTTPException(400, "Failed update token")


@router.get("/me")
@limiter.limit("60/minute")  
async def get_current_user(
    request: Request,
    user: Annotated[UserTypes, Depends(get_current_user_from_token)],
):
    """Get current user"""
    if not user:
        raise HTTPException(401, "Authentication error")

    if not await validate_access_token(user.accessToken or ""):
        raise HTTPException(401, "Authentication error")

    user_data = UserTypes.model_validate(user)
    user_dict = user_data.model_dump(mode="json")

    return CurrentUserDto(**user_dict)


@router.get("/verify/{id_token}", status_code=200, response_model=None)
async def validate_email(
    id_token: str,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Verify email address"""
    await auth_service.verify_email(db, id_token)
    return {"message": "Email verified"}

@router.post(
    "/forgot-password",
    status_code=200,
    responses={200: {"description": "Password reset email sent if user exists"}},
)
async def forgot_password(
    request_data: PasswordResetRequestModel,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Request a password reset email"""
    await auth_service.request_password_reset(db, request_data.email)
    # Always return success message to prevent email enumeration
    return {"message": "If that email is in our database, we will send a password reset link"}


@router.post(
    "/reset-password",
    status_code=200,
    responses={200: {"description": "Password successfully reset"}},
)
async def reset_password(
    reset_data: PasswordResetConfirmModel,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Reset password using token received via email"""
    await auth_service.reset_password(
        db, 
        token=reset_data.token, 
        new_password=reset_data.new_password
    )
    return {"message": "Password successfully updated"}
