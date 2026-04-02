from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


# Shared properties
class UserBase(BaseModel):
    """Base user properties shared across schemas."""

    email: Optional[EmailStr] = Field(
        None,
        title="Email",
        description="User email address",
        examples=["user@example.com"],
    )
    is_active: Optional[bool] = Field(
        True,
        title="Is Active",
        description="Whether the user account is active",
        examples=[True],
    )
    is_superuser: bool = Field(
        False,
        title="Is Superuser",
        description="Whether the user has superuser privileges",
        examples=[False],
    )
    full_name: Optional[str] = Field(
        None,
        title="Full Name",
        description="User full name",
        examples=["John Doe"],
        max_length=100,
    )


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user."""

    email: EmailStr = Field(
        ...,
        title="Email",
        description="User email address (required for creation)",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        title="Password",
        description="User password (min 8 characters)",
        min_length=8,
        max_length=100,
        examples=["SecureP@ss123"],
    )


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating an existing user."""

    password: Optional[str] = Field(
        None,
        title="Password",
        description="New password (min 8 characters). Only include to change password.",
        min_length=8,
        max_length=100,
        examples=["NewSecureP@ss123"],
    )


class UserInDBBase(UserBase):
    """Base schema for user data stored in database."""

    id: Optional[int] = Field(
        None,
        title="ID",
        description="Unique user identifier",
        examples=[1],
    )

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class User(UserInDBBase):
    """Schema returned by the API for user data."""

    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    """Internal schema for user data in database (includes hashed password)."""

    hashed_password: str = Field(
        ...,
        title="Hashed Password",
        description="Bcrypt hashed password",
    )
