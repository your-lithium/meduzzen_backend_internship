from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    username: str
    email: EmailStr
    disabled: bool


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    password: str | None = None


class UserDetailResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    disabled: bool
