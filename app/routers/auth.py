from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse, SignInRequest
from app.services.user import get_user_service
from app.services.auth import get_auth_service, Token
from app.db.database import get_session


router = APIRouter(prefix="/auth", tags=["Auth Methods"])


@router.post("/signin", response_model=Token)
async def signin(
    request: SignInRequest,
    auth_service=Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
) -> Token:
    access_token = await auth_service.signin(request=request, session=session)

    return Token(access_token=access_token)


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest,
    user_service=Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    user = await user_service.create_user(user=user, session=session)

    return user
