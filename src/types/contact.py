from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class ContactDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(
        json_schema_extra={"example": "Bob"}
    )
    last_name: str = Field(
        json_schema_extra={"example": "Marley"}
    )
    email: str = Field(
        json_schema_extra={"example": "bob@mail.com"}
    )
    phone: Optional[str] = Field(
        default=None,
        json_schema_extra={"example": "+380501112233"}
    )
    birthday: datetime = Field(
        json_schema_extra={"example": "1990-07-13T00:00:00"}
    )
    description: Optional[str] = Field(
        default=None,
        json_schema_extra={"example": "Friend from school"}
    )
    
    
class ContactDtoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"}
    )

    first_name: str = Field(
        json_schema_extra={"example": "Bob"}
    )
    last_name: str = Field(
        json_schema_extra={"example": "Marley"}
    )
    email: str = Field(
        json_schema_extra={"example": "bob@mail.com"}
    )
    phone: Optional[str] = Field(
        default=None,
        json_schema_extra={"example": "+380501112233"}
    )
    birthday: datetime = Field(
        json_schema_extra={"example": "1990-07-13T00:00:00"}
    )
    description: Optional[str] = Field(
        default=None,
        json_schema_extra={"example": "Friend from school"}
    )
    
class UpdateContactDto(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={

            "example": {

                "first_name": "Robert",

                "last_name": "Marley",

                "email": "new@mail.com",

                "phone": "+380671234567",

                "birthday": "1990-07-13T00:00:00",
                
                 "description": "Best friend from school"

            }

        }

    )
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthday: Optional[datetime] = None
    description: Optional[str] = None