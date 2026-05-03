from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.user import UserModel


class ContactModel(Base):
    """SQLAlchemy model representing a contact record."""
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, unique=True, index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    birthday: Mapped[date] = mapped_column(Date())
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="contacts"
    )