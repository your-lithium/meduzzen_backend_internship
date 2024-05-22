from pydantic import BaseModel, EmailStr
from typing import Optional, List


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    username: str
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class SignUpRequest(BaseModel):
    id: int
    name: str = 'John Doe'
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
    id: int
    name: str
    username: str
    email: EmailStr
