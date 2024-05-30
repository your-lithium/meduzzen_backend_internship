import bcrypt
from sqlalchemy.future import select
from uuid import UUID

from app.db.database import get_session
from app.db.user_model import User
from app.schemas.user_schemas import UserUpdateRequest, SignUpRequest
from app.core.logger import logger


class UserRepo:
    """Represents a repository pattern to perform CRUD on User model.
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
        query = select(User)

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
            
        async for session in get_session():
            result = await session.execute(query)
            users = result.scalars().all()
        
        return users
    
    async def get_user(
        self,
        user_id: UUID
    ) -> User | None:
        """Get details for one user.

        Args:
            user_id (UUID): The user's ID.

        Returns:
            User | None: User details.
        """
        async for session in get_session():
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
        
        return user
    
    async def create_user(
        self,
        user: SignUpRequest
    ) -> User | None:
        """Create a new user.

        Args:
            user (SignUpRequest): Details for creating a new user.

        Returns:
            User | None: Details of the new user.
        """
        logger.info(f"Received a signup request")
    
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=hashed_password.decode("utf-8")
        )

        async for session in get_session():
            existing_user_query = await session.execute(
            select(User).where((User.username == new_user.username) | (User.email == new_user.email))
            )
            existing_user = existing_user_query.scalar()
            
            if existing_user:
                logger.info("User with the same username or email already exists")
                return None
            
            session.add(new_user)
            await session.commit()
        
        logger.info("New user created successfully")
        return new_user
        
    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdateRequest,
    ) -> User | None:
        """Update an existing user.

        Args:
            user_id (UUID): The user's ID.
            user_update (UserUpdateRequest): The details which to update in a user.

        Returns:
            User | None: Details of the updated user.
        """
        logger.info(f"Received request to update user with ID {user_id}")

        async for session in get_session():
            result = await session.execute(select(User).where(User.id == user_id))
            existing_user = result.scalars().first()

            if not existing_user:
                return None

            attributes = ['name', 'username', 'email']
            
            for attr in attributes:
                new_value = getattr(user_update, attr)
                if new_value is not None:
                    setattr(existing_user, attr, new_value)    

            if user_update.password is not None:
                hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
                existing_user.password_hash = hashed_password.decode("utf-8")

            await session.commit()
            await session.refresh(existing_user)

        logger.info(f"User with ID {user_id} updated successfully")
        return existing_user
    
    async def delete_user(
        self,
        user_id: UUID
    ) -> UUID | None:
        """Delete a user.

        Args:
            user_id (UUID): The user's ID.

        Returns:
            UUID | None: ID of the deleted user.
        """
        logger.info(f"Received request to delete user with ID {user_id}")

        async for session in get_session():
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()

            if not user:
                return None

            await session.delete(user)
            await session.commit()

        logger.info(f"User with ID {user_id} deleted successfully")
        return user_id
    
    async def check_unique_fields(
        self,
        user_update: UserUpdateRequest,
    ) -> bool:
        """Check if the values for unique fields have already been used.

        Args:
            user_update (UserUpdateRequest): The details which to check.

        Returns:
            bool: Whether or not details have already been taken.
        """
        async for session in get_session():
            existing_user_query = await session.execute(
            select(User).where((User.username == user_update.username) | (User.email == user_update.email))
            )
            existing_user = existing_user_query.scalar()
        
        if existing_user:
            return False
        
        return True
