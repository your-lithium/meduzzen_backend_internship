from pydantic import BaseModel, EmailStr
from typing import Optional, List


class User(BaseModel):
    uid: int
    name: str
    username: str
    email: EmailStr
    password: str


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
    users: List[User]


class UserDetailResponse(BaseModel):
    uid: int
    name: str
    username: str
    email: EmailStr
