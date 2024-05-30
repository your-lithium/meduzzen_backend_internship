from fastapi import APIRouter

from app.schemas.user_schemas import SignUpRequest, UserDetailResponse
from app.services.controllers.auth import AuthService


router = APIRouter(prefix="/auth")
auth_service = AuthService()

@router.post("/signup", response_model=UserDetailResponse)
async def create_user(
    user: SignUpRequest
    ):
    user = await auth_service.create_user(user=user)
    
    return UserDetailResponse(
        id=user.id,
        name=user.name,
        username=user.username, 
        email=user.email
        )
