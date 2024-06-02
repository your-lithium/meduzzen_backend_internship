from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse
from app.services.user import UserService
from app.services.auth import AuthService, Token
from app.db.database import get_session
from app.db.user_model import User
from app.core.config import config


router = APIRouter(prefix="/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")


def get_user_service():
    return UserService()


def get_auth_service():
    return AuthService()


@router.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


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
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    current_user: User = await auth_service.get_current_active_user(
        secret_key=config.oauth2_secret_key,
        algorithm=config.oauth2_algorithm,
        token=token,
        session=session,
    )
    return current_user


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.create_user(user=user, session=session)

    return user
