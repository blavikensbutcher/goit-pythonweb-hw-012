import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import Role


class UserCreateResponse(BaseModel):
    message: str = "Successfully registered"


class UserTypes(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    email: EmailStr
    isVerified: bool
    password: str
    isBanned: bool
    role: Role
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    type: str = "Bearer"
    accessToken: Optional[str]
    refreshToken: Optional[str]


class UserAccessTokenUpdate(BaseModel):
    refreshToken: str = Field(
        ...,
        description="Refresh token to update access token",
        json_schema_extra={
            "examples": [
                "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInN1YiI6Ijk0YjUyMWI0LWZhZGYtNGVlNi1hZTc1LTdhN2M0ZjVhYjY3MiIsImV4cCI6MjA2ODk5NjQ5MSwiaWF0IjoxNzUzNjM2NDkxfQ."
                "DqSYiHwH2XB1hQjRvCO0V45YcgSQRLFD0mDivGI8n-3r0KCs0Olw7ic_9UnKbMeiwB2yAy2rzuEwkPsdMVEW126R1FqUeeakLGD5IDZDcmwNpC1SNBVvmvahGAyGnZSrHGsYBxsKtTQqtm_9IE9gjKD9U85oX8xxhCQuwJGJh3R-"
                "vWpcB9Zqnka7aQZWHSisXRwfNEqdmgGiJ0RdEqV9QzwIq7qbvPiLZPMODBn15ZZj62OhhNKrwaqSzZgU9XiNErberfK0_8Enx2lZNou5_duCRVKzxDuvbJDG2Yzb5Yhhhq3ltGB-AhSIGPpGPk2S9pSzDQ8GmA_mWUCkRUzbsg"
            ]
        },
    )


class UserAccessTokenUpdateResponse(BaseModel):
    type: str = "Bearer"
    accessToken: Optional[str]


class FindUserByIdResponse(BaseModel):
    name: str
    email: str
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None
    isVerified: bool = False
    isBanned: bool = False
    role: Role = Role.USER

    model_config = ConfigDict(from_attributes=True)


class CurrentUserDto(BaseModel):
    id: str
    name: str
    email: str
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None
    isBanned: bool = False
    role: Role = Role.USER

    model_config = ConfigDict(from_attributes=True)


class UpdateUserResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    isVerified: Optional[bool] = None
    isBanned: Optional[bool] = None
    role: Optional[Role] = None
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)
