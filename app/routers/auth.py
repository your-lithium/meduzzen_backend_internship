from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse
from app.services.user import UserService
from app.db.database import get_session
from app.db.user_model import User


router = APIRouter(prefix="/auth")


def get_user_service():
    return UserService()


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service)
    ):
    user = await user_service.create_user(user=user, session=session)
    
    return user
