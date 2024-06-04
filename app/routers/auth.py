from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse, SignInRequest
from app.services.user import UserService
from app.services.auth import AuthService, Token
from app.db.database import get_session


router = APIRouter(prefix="/auth")


@router.post("/signin")
async def signin(
    request: SignInRequest,
    session: AsyncSession = Depends(get_session),
) -> Token:
    access_token = await AuthService.signin(request=request, session=session)

    return Token(access_token=access_token, token_type="bearer")


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await UserService.create_user(user=user, session=session)

    return user
