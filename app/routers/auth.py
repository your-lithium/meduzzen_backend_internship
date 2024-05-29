from fastapi import APIRouter

from app.schemas.user_schemas import *
from app.services.db_requests.auth import AuthService


router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest
    ):
    
    return AuthService.create_user(user=user)
