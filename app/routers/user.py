from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import UserDetailResponse, UserUpdateRequest, UserResponse
from app.services.user import UserService
from app.services.auth import AuthService
from app.db.database import get_session
from app.db.user_model import User
from app.core.security import auth_scheme


router = APIRouter(prefix="/users")


@router.get("", response_model=list[UserResponse])
async def read_all_users(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    users = await UserService.get_all_users(limit=limit, offset=offset, session=session)

    return users


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user_by_id(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    user = await UserService.get_user_by_id(user_id=user_id, session=session)

    return user


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await UserService.update_user(
        user_id=user_id, user_update=user_update, session=session
    )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    await UserService.delete_user(user_id=user_id, session=session)

    return None


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user(
    token: str | None = Depends(auth_scheme),
    session: AsyncSession = Depends(get_session),
):
    print(token)
    current_user: User = await AuthService.get_current_active_user(
        token=token.credentials,
        session=session,
    )
    return current_user
