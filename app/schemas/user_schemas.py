from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    password_hash: str
    disabled: bool

    class Config:
        from_attributes = True


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    id: Optional[str] = None
    name: str
    username: str
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    email: str | None = None
    password: str | None = None


class UserDetailResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    disabled: bool
