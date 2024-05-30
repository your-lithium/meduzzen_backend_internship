from uuid import UUID
from pydantic import Json

from app.db.user_model import User
from app.schemas.user_schemas import UserUpdateRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import UserNotFoundError, UserAlreadyExistsError


user_repo = UserRepo()

class UserService:    
    async def get_all_users(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        users: list[User] = await user_repo.get_all_users(limit=limit, offset=offset)
        
        return users
    
    async def get_user(
        self,
        user_id: UUID
    ) -> User:
        user: User | None = await user_repo.get_user(user_id=user_id)
        
        if user is None:
            raise UserNotFoundError(user_id)
        
        return user
        
    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
    ) -> User:
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
        deleted_user = await user_repo.delete_user(user_id=user_id)
        
        if deleted_user is None:
            raise UserNotFoundError(user_id)
                
        return {"detail": "User deleted successfully"}
