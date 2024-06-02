import bcrypt
import jwt
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone

from app.db.user_model import User
from app.schemas.user_schemas import SignInRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import (
    UserNotFoundError,
    IncorrectPasswordError,
    UnauthorizedError,
    InactiveUserError,
)
from app.db.database import get_session


user_repo = UserRepo()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr | None = None


class AuthService:
    """Represents a service for handling authentication requests."""

    def __init__(
        self,
    ):
        pass

    def create_access_token(
        self,
        data: dict,
        secret_key: str,
        algorithm: str,
        expires_delta: timedelta | None = None,
    ):
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        return encoded_jwt

    async def get_current_user(
        self,
        secret_key: str,
        algorithm: str,
        token: str,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            print(f"Decoded Payload: {payload}")
            email: str = payload.get("sub")
            print(f"Email: {email}")
            if email is None:
                raise UnauthorizedError
            token_data = TokenData(email=email)
        except ExpiredSignatureError:
            raise UnauthorizedError("Token has expired")
        except DecodeError:
            raise UnauthorizedError("Error decoding token")
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")

        user = await user_repo.get_user_by_email(
            user_email=token_data.email, session=session
        )
        if user is None:
            raise UserNotFoundError(identifier=token_data.email)

        return user

    async def get_current_active_user(
        self,
        secret_key: str,
        algorithm: str,
        token: str,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        current_user: User = await self.get_current_user(
            secret_key=secret_key, algorithm=algorithm, token=token, session=session
        )

        if current_user.disabled:
            raise InactiveUserError

        return current_user

    async def signin(
        self,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, str]:
        request = SignInRequest(email=form_data.username, password=form_data.password)

        user = await user_repo.get_user_by_email(
            user_email=request.email, session=session
        )
        if user is None:
            raise UserNotFoundError(identifier=request.email)

        if not bcrypt.checkpw(
            request.password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            raise IncorrectPasswordError

        return user
