from app.db.user_model import User
from app.schemas.user_schemas import SignUpRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import UserAlreadyExistsError


user_repo = UserRepo()

class AuthService:
    async def create_user(
        self,
        user: SignUpRequest
    ) -> User:
        user: User | None = await user_repo.create_user(user=user)
        
        if user is None:
            raise UserAlreadyExistsError
        
        return user
