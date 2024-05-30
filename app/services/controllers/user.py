from uuid import UUID
from pydantic import Json

from app.db.user_model import User
from app.schemas.user_schemas import UserUpdateRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import UserNotFoundError, UserAlreadyExistsError


user_repo = UserRepo()

class UserService:
    """Represents a service for handling requests to User model.
    """
    
    async def get_all_users(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        """Get a list of users.

        Args:
            limit (int | None, optional): How much users to get. Defaults to None.
            offset (int | None, optional): Where to start getting users. Defaults to None.

        Returns:
            list[User]: The list of users.
        """
        users: list[User] = await user_repo.get_all_users(limit=limit, offset=offset)
        
        return users
    
    async def get_user(
        self,
        user_id: UUID
    ) -> User:
        """Get details for one user.

        Args:
            user_id (UUID): The user's ID.

        Raises:
            UserNotFoundError: If the requested user does not exist.

        Returns:
            User: User details.
        """
        user: User | None = await user_repo.get_user(user_id=user_id)
        
        if user is None:
            raise UserNotFoundError(user_id)
        
        return user
        
    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
    ) -> User:
        """Update an existing user.

        Args:
            user_id (UUID): The user's ID.
            user_update (UserUpdateRequest): The details which to update in a user.

        Raises:
            UserAlreadyExistsError: If the details provided have already been used but have to be unique.
            UserNotFoundError: If the requested user does not exist.

        Returns:
            User: Details of the updated user.
        """
        request_ok: bool = await user_repo.check_unique_fields(user_update=user_update)
        
        if not request_ok:
            raise UserAlreadyExistsError
        
        user: User | None = await user_repo.update_user(user_id=user_id, user_update=user_update)
        
        if user is None:
            raise UserNotFoundError(user_id)
            
        return user
    
    async def delete_user(
        self,
        user_id: UUID
    ) -> Json:
        """Delete a user.

        Args:
            user_id (UUID): The user's ID.

        Raises:
            UserNotFoundError: If the requested user does not exist.

        Returns:
            Json: The response of operation being completed successfully.
        """
        deleted_user = await user_repo.delete_user(user_id=user_id)
        
        if deleted_user is None:
            raise UserNotFoundError(user_id)
                
        return {"detail": "User deleted successfully"}
