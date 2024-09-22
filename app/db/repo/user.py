from typing import Type

import bcrypt
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import User
from app.db.repo.base import BaseRepo
from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest


class UserRepo(BaseRepo[User]):
    """Represents a repository pattern to perform CRUD on User model."""

    @classmethod
    def get_model(cls) -> Type[User]:
        return User

    @staticmethod
    async def get_user_by_email(
        user_email: EmailStr, session: AsyncSession = Depends(get_session)
    ) -> User | None:
        return await UserRepo.get_by_fields(
            fields=User.email, values=user_email, session=session
        )

    @staticmethod
    async def get_user_by_username(
        user_username: str, session: AsyncSession = Depends(get_session)
    ) -> User | None:
        return await UserRepo.get_by_fields(
            fields=User.username, values=user_username, session=session
        )

    @staticmethod
    async def create_user(
        user: SignUpRequest, session: AsyncSession = Depends(get_session)
    ) -> User:
        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
        new_user = User(
            id=user.id,
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=hashed_password.decode("utf-8"),
        )
        return await UserRepo.create(entity=new_user, session=session)

    @staticmethod
    async def update_user(
        existing_user: User,
        user_update: UserUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        update_data = user_update.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        if user_update.password is not None:
            hashed_password = bcrypt.hashpw(
                user_update.password.encode("utf-8"), bcrypt.gensalt()
            )
            update_data["password_hash"] = hashed_password.decode("utf-8")
        return await UserRepo.update(
            entity=existing_user, update_data=update_data, session=session
        )
