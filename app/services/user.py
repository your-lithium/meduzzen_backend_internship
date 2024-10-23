from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import User
from app.db.repo.user import UserRepo
from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest
from app.services.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from app.services.permissions import PermissionService


def get_user_service():
    return UserService()


class UserService:
    """Represents a service for handling requests to User model."""

    async def get_all_users(
        self,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[User]:
        """Get a list of users.

        Args:
            limit (int, optional):
                How much users to get. Defaults to 10.
                If None, retrieve all records.
            offset (int, optional):
                Where to start getting users. Defaults to 0.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The list of users.
        """
        users: list[User] = await UserRepo.get_all(
            limit=limit, offset=offset, session=session
        )
        return users

    async def get_user_by_id(
        self, user_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> User:
        """Get details for one user.

        Args:
            user_id (UUID): The user's ID.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            UserNotFoundError: If the requested user does not exist.

        Returns:
            User: User details.
        """
        user: User | None = await UserRepo.get_by_id(record_id=user_id, session=session)

        if user is None:
            raise UserNotFoundError(user_id)

        return user

    async def create_user(
        self, user: SignUpRequest, session: AsyncSession = Depends(get_session)
    ) -> User:
        """Creates a new user from details provided.

        Args:
            user (SignUpRequest): Details for the new user
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Returns:
            User: The created user.
        """
        check_email: User | None = await UserRepo.get_user_by_email(
            user_email=user.email, session=session
        )
        if check_email is not None:
            raise EmailAlreadyExistsError(object_value=user.email)

        check_username: User | None = await UserRepo.get_user_by_username(
            user_username=user.username, session=session
        )
        if check_username is not None:
            raise UsernameAlreadyExistsError(object_value=user.username)

        new_user: User = await UserRepo.create_user(user=user, session=session)

        return new_user

    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """Update an existing user.

        Args:
            user_id (UUID): The user's ID.
            user_update (UserUpdateRequest): The details which to update in a user.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            UserNotFoundError: If the requested user does not exist.
            UsernameAlreadyExistsError: If the username provided has already been used.

        Returns:
            User: Details of the updated user.
        """
        PermissionService.grant_user_permission(
            user_id=user_id, current_user_id=current_user.id, operation="update"
        )

        if user_update.username:
            check_username: User | None = await UserRepo.get_user_by_username(
                user_username=user_update.username, session=session
            )
            if check_username is not None:
                raise UsernameAlreadyExistsError(object_value=user_update.username)

        updated_user = await UserRepo.update_user(
            existing_user=current_user, user_update=user_update, session=session
        )
        return updated_user

    async def delete_user(
        self,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Delete a user.

        Args:
            user_id (UUID): The user's ID.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            UserNotFoundError: If the requested user does not exist.
        """
        PermissionService.grant_user_permission(
            user_id=user_id, current_user_id=current_user.id, operation="delete"
        )
        await UserRepo.delete(entity=current_user, session=session)
