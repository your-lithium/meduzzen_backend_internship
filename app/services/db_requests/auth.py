from app.schemas.user_schemas import *
from app.db.repo.auth import AuthRepo


class AuthService:
    async def create_user(
        self,
        user: SignUpRequest
    ) -> UserDetailResponse:
        # check permissions later
        
        return AuthRepo(user=user)
