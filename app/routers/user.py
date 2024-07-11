from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import UserDetailResponse, UserUpdateRequest, UserResponse
from app.services.user import get_user_service, UserService
from app.services.auth import get_current_user
from app.db.database import get_session
from app.db.models import User


router = APIRouter(prefix="/users", tags=["User Methods"])


@router.get("", response_model=list[UserResponse])
async def read_all_users(
    limit: int = 10,
    offset: int = 0,
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    users = await user_service.get_all_users(
        limit=limit, offset=offset, session=session
    )

    return users


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    user = await user_service.get_user_by_id(user_id=user_id, session=session)

    return user


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    user = await user_service.update_user(
        user_id=user_id,
        user_update=user_update,
        current_user=current_user,
        session=session,
    )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    await user_service.delete_user(
        user_id=user_id, current_user=current_user, session=session
    )
