from uuid import UUID

from app.schemas.user_schemas import *
from app.db.repo.user import UserRepo


class UserService:    
    async def get_all_users(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ):
        # check permissions later
        
        return UserRepo.get_all_users(limit=limit, offset=offset)
    
    async def get_user(
        self,
        user_id: UUID
    ):
        # check permissions later
        
        return UserRepo.get_user(user_id=user_id)
        
    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
    ):
        # check permissions later
        
        return UserRepo.update_user(user_id=user_id, user_update=user_update)
    
    async def delete_user(
        self,
        user_id: UUID
    ):
        # check permissions later
        
        return UserRepo.delete_user(user_id=user_id)
