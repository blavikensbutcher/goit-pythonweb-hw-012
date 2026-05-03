import enum
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.contacts import ContactModel


class Role(str, Enum):
    """Role enum for Pydantic models (string-based)"""
    ADMIN = "ADMIN"
    PREMIUM = "PREMIUM"
    USER = "USER"
    TRAINER = "TRAINER"


class RoleEnum(enum.Enum):
    """Role enum for SQLAlchemy (enum-based)"""
    ADMIN = "ADMIN"
    PREMIUM = "PREMIUM"
    USER = "USER"
    TRAINER = "TRAINER"


class UserModel(Base):
    """SQLAlchemy model for users table"""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,  
        unique=True,
        index=True,
    )

    # Basic user information
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    # Status flags
    isVerified: Mapped[bool] = mapped_column(Boolean, default=False)
    isBanned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Authentication tokens
    accessToken: Mapped[str | None] = mapped_column(String, nullable=True)
    refreshToken: Mapped[str | None] = mapped_column(String, nullable=True)

    # User role with enum type
    role: Mapped[RoleEnum] = mapped_column(
        SqlEnum(RoleEnum), default=RoleEnum.USER, nullable=False
    )

    # Timestamps with timezone awareness
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    contacts: Mapped[list["ContactModel"]] = relationship(
        "ContactModel",
        back_populates="user",
        cascade="all, delete-orphan",   
    )


class CreateUserModel(BaseModel):
    """DTO for creating new user"""
    name: Optional[str] = Field(default=None, json_schema_extra={"example": "John Doe"})
    email: EmailStr = Field(..., json_schema_extra={"example": "john.doe@mail.com"})
    password: str = Field(
        ..., min_length=6, json_schema_extra={"example": "_1jUie_1328!#$"}
    )


class UpdateUserModel(BaseModel):
    """DTO for updating user fields"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    isVerified: Optional[bool] = None
    refreshToken: Optional[str] = None
    accessToken: Optional[str] = None


class AuthCredentials(BaseModel):
    """DTO for user authentication"""
    email: EmailStr = Field(..., json_schema_extra={"example": "test@mail.com"})
    password: str = Field(..., json_schema_extra={"example": "_1jUie_1328!#$"})