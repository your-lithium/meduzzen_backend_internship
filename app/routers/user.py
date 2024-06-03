from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import UserDetailResponse, UserUpdateRequest, UserResponse
from app.services.user import UserService
from app.db.database import get_session
from app.db.user_model import User
from app.routers.auth import get_current_user
from app.services.exceptions import AccessDeniedError


router = APIRouter(prefix="/users")


def get_user_service():
    return UserService()


@router.get("", response_model=list[UserResponse])
async def read_all_users(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    users = await user_service.get_all_users(
        limit=limit, offset=offset, session=session
    )

    return users


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user_by_id(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_user_by_id(user_id=user_id, session=session)

    return user


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    if user_id != current_user.id:
        raise AccessDeniedError(
            "You are not allowed to update other users' information"
        )

    user = await user_service.update_user(
        user_id=user_id, user_update=user_update, session=session
    )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    if user_id != current_user.id:
        raise AccessDeniedError("You are not allowed to delete other users")

    await user_service.delete_user(user_id=user_id, session=session)

    return None
