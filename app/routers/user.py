from fastapi import APIRouter
from uuid import UUID

from app.schemas.user_schemas import *
from app.services.db_requests.user import UserService

router = APIRouter(prefix="/user")


@router.get("/all", response_model=UsersListResponse)
async def read_all_users(
    limit: int | None = None,
    offset: int | None = None,
    ):

    return UserService.get_all_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user_by_id(
    user_id: UUID
    ):
    
    return UserService.get_user(user_id=user_id)


@router.patch("/update/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest
    ):
    
    return UserService.update_user(user_id=user_id, user_update=user_update)


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: UUID
    ):
    
    return UserService.delete_user(user_id=user_id)
