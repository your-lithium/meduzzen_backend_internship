from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from datetime import timedelta

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse
from app.services.user import UserService
from app.services.auth import AuthService, Token
from app.db.database import get_session
from app.db.user_model import User
from app.core.config import config


router = APIRouter(prefix="/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")
auth0_scheme = HTTPBearer()


async def get_token(
    oauth2_token: str | None = Depends(oauth2_scheme),
    auth0_token: HTTPAuthorizationCredentials | None = Depends(auth0_scheme),
) -> str | None:
    if oauth2_token:
        return oauth2_token
    elif auth0_token:
        return auth0_token.credentials
    else:
        return None


def get_user_service():
    return UserService()


def get_auth_service():
    return AuthService()


@router.get("/items/")
async def read_items(token: str | None = Depends(get_token)):
    if token:
        return {"token": token}
    else:
        return {"message": "No token provided"}


@router.post("/signin")
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    user = await auth_service.signin(form_data=form_data, session=session)

    access_token_expires = timedelta(days=config.oauth2_access_token_expire_days)
    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        secret_key=config.oauth2_secret_key,
        algorithm=config.oauth2_algorithm,
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def get_current_user(
    token: str | None = Depends(get_token),
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    current_user: User = await auth_service.get_current_active_user(
        token=token,
        oauth2_secret_key=config.oauth2_secret_key,
        oauth2_algorithm=config.oauth2_algorithm,
        auth0_domain=config.auth0_domain,
        auth0_algorithms=config.auth0_algorithms,
        auth0_audience=config.auth0_audience,
        session=session,
    )
    return current_user


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> User:
    user = await user_service.create_user(user=user, session=session)

    return user
