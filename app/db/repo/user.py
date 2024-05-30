import bcrypt
from sqlalchemy.future import select
from uuid import UUID

from app.db.database import get_session
from app.db.user_model import User
from app.schemas.user_schemas import UserUpdateRequest, SignUpRequest
from app.core.logger import logger


class UserRepo:
    async def get_all_users(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
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
        async for session in get_session():
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
        
        return user
    
    async def create_user(
        self,
        user: SignUpRequest
    ) -> User | None:
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
    ) -> User | None:
        async for session in get_session():
            existing_user_query = await session.execute(
            select(User).where((User.username == user_update.username) | (User.email == user_update.email))
            )
            existing_user = existing_user_query.scalar()
        
        if existing_user:
            return False
        
        return True
