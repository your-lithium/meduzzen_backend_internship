import bcrypt
from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from pydantic import EmailStr

from app.db.database import get_session
from app.db.models import User
from app.schemas.user_schemas import UserUpdateRequest, SignUpRequest
from app.core.logger import logger


class UserRepo:
    """Represents a repository pattern to perform CRUD on User model."""

    @staticmethod
    async def get_all_users(
        limit: int = 10, offset: int = 0, session: AsyncSession = Depends(get_session)
    ) -> list[User]:
        """Get a list of users.

        Args:
            limit (int, optional): How much users to get. Defaults to 10.
            offset (int, optional): Where to start getting users. Defaults to 0.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The list of users.
        """
        result = await session.execute(select(User).limit(limit).offset(offset))
        users = result.scalars().all()

        return users

    @staticmethod
    async def get_user_by_id(
        user_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> User | None:
        """Get details for one user via their ID.

        Args:
            user_id (UUID): The user's ID.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User | None: User details.
        """
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        return user

    @staticmethod
    async def get_user_by_email(
        user_email: EmailStr, session: AsyncSession = Depends(get_session)
    ) -> User | None:
        """Get details for one user via their email.

        Args:
            user_email (EmailStr): The email which to check.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User | None: User details.
        """
        result = await session.execute(select(User).where(User.email == user_email))
        user = result.scalars().first()

        return user

    @staticmethod
    async def get_user_by_username(
        user_username: str, session: AsyncSession = Depends(get_session)
    ) -> User | None:
        """Get details for one user via their username.

        Args:
            user_username (str): The username which to check.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User | None: User details.
        """
        result = await session.execute(
            select(User).where(User.username == user_username)
        )
        user = result.scalars().first()

        return user

    @staticmethod
    async def create_user(
        user: SignUpRequest, session: AsyncSession = Depends(get_session)
    ) -> User:
        """Create a new user.

        Args:
            user (SignUpRequest): Details for creating a new user.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User: Details of the new user.
        """
        logger.info("Received a signup request")

        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

        new_user = User(
            id=user.id,
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=hashed_password.decode("utf-8"),
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info("New user created successfully")
        return new_user

    @staticmethod
    async def update_user(
        existing_user: User,
        user_update: UserUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """Update an existing user.

        Args:
            existing_user (User): The existing user to update
            user_update (UserUpdateRequest): The details which to update in a user.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User: Details of the updated user.
        """
        logger.info(f"Received request to update user with ID {existing_user.id}")

        for attr in user_update.__dict__:
            value = getattr(user_update, attr)
            if value is not None:
                setattr(existing_user, attr, value)

        if user_update.password is not None:
            hashed_password = bcrypt.hashpw(
                user_update.password.encode("utf-8"), bcrypt.gensalt()
            )
            existing_user.password_hash = hashed_password.decode("utf-8")

        await session.commit()
        await session.refresh(existing_user)

        logger.info(f"User with ID {existing_user.id} updated successfully")
        return existing_user

    @staticmethod
    async def delete_user(
        user: User, session: AsyncSession = Depends(get_session)
    ) -> None:
        """Delete a user.

        Args:
            user (User): The existing user to delete.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to delete user with ID {user.id}")

        await session.delete(user)
        await session.commit()

        logger.info(f"User with ID {user.id} deleted successfully")
