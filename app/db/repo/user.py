import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from pydantic import Json

from app.db.database import get_session
from app.db.user_model import User
from app.schemas.user_schemas import *
from app.core.logger import logger


class UserRepo:
    def __init__(self) -> None:
        self._session = get_session
        
    async def get_all_users(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UsersListResponse:
        query = select(User)

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        result = await self._session.execute(query)
        users = result.scalars().all()
        
        return UsersListResponse(users=users)
    
    async def get_user(
        self,
        user_id: UUID
    ) -> UserDetailResponse:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with ID {user_id} not found")
        
        return UserDetailResponse(
            user_id=user.id,
            name=user.name,
            username=user.username,
            email=user.email
        )
        
    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
    ) -> UserDetailResponse:
        logger.info(f"Received request to update user with ID {user_id}")

        result = await self._session.execute(select(User).where(User.id == user_id))
        existing_user = result.scalars().first()

        if not existing_user:
            logger.error(f"User with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")

        if user_update.name is not None:
            existing_user.name = user_update.name
        if user_update.username is not None:
            existing_user.username = user_update.username
        if user_update.email is not None:
            existing_user.email = user_update.email
        if user_update.password is not None:
            hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
            existing_user.password_hash = hashed_password.decode('utf-8')

        try:
            await self._session.commit()
            await self._session.refresh(existing_user)
        except IntegrityError:
            await self._session.rollback()
            logger.warning(f"Username or email already exists")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

        logger.info(f"User with ID {user_id} updated successfully")
        
        return UserDetailResponse(
            id=existing_user.id,
            name=existing_user.name,
            username=existing_user.username,
            email=existing_user.email
        )
    
    async def delete_user(
        self,
        user_id: UUID
    ) -> Json:
        logger.info(f"Received request to delete user with ID {user_id}")

        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")

        await self._session.delete(user)
        await self._session.commit()

        logger.info(f"User with ID {user_id} deleted successfully")
        return {"detail": "User deleted successfully"}
