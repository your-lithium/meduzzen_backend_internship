from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    password_hash: str
    
    class Config:
        from_attributes = True


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UsersListResponse(BaseModel):
    users: List[UserResponse]


class UserDetailResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
