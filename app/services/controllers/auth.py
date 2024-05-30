from app.db.user_model import User
from app.schemas.user_schemas import SignUpRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import UserAlreadyExistsError


user_repo = UserRepo()

class AuthService:
    """Represents a service for handling authentication requests.
    """
    
    async def create_user(
        self,
        user: SignUpRequest
    ) -> User:
        """Creates a new user from details provided.

        Args:
            user (SignUpRequest): Details for the new user

        Raises:
            UserAlreadyExistsError: If a user with details provided exists already.

        Returns:
            User: The created user.
        """
        user: User | None = await user_repo.create_user(user=user)
        
        if user is None:
            raise UserAlreadyExistsError
        
        return user
