import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError

from app.db.database import get_session
from app.db.user_model import User
from app.schemas.user_schemas import *
from app.core.logger import logger


class AuthRepo:  
    def __init__(self) -> None:
        self._session = get_session
    
    async def create_user(
        self,
        user: SignUpRequest
    ) -> UserDetailResponse:
        logger.info(f"Received a signup request")
    
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=hashed_password.decode('utf-8')
        )

        self._session.add(new_user)
        try:
            await self._session.commit()
            await self._session.refresh(new_user)
        except RequestValidationError as e:
            logger.error(f"Validation error: {e.errors()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )
        except IntegrityError:
            await self._session.rollback()
            logger.error(f"Username or email already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )

        return UserDetailResponse(
            id=new_user.id,
            name=new_user.name,
            username=new_user.username,
            email=new_user.email
        )