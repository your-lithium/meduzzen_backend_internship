from fastapi import APIRouter
from uuid import UUID

from app.schemas.user_schemas import UsersListResponse, UserDetailResponse, UserUpdateRequest
from app.services.controllers.user import UserService


router = APIRouter(prefix="/users")
user_service = UserService()

@router.get("", response_model=UsersListResponse)
async def read_all_users(
    limit: int | None = None,
    offset: int | None = None,
    ):
    users = await user_service.get_all_users(limit=limit, offset=offset)
    
    return UsersListResponse(users=users)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user_by_id(
    user_id: UUID
    ):
    user = await user_service.get_user(user_id=user_id)
    
    return UserDetailResponse(
        id=user.id,
        name=user.name,
        username=user.username, 
        email=user.email
        )


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest
    ):
    user = await user_service.update_user(user_id=user_id, user_update=user_update)
    
    return UserDetailResponse(
        id=user.id,
        name=user.name,
        username=user.username, 
        email=user.email
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID
    ):
    
    return await user_service.delete_user(user_id=user_id)
