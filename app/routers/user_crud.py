import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError
from uuid import UUID

from app.db.database import get_session
from app.db.user_model import User
from app.schemas.user_schemas import *
from app.core.logger import logger

router = APIRouter(prefix="/user")


@router.get("/", response_model=UsersListResponse)
async def read_all_users(limit:Optional[int] = None, offset:Optional[int] = None, session: AsyncSession = Depends(get_session)):
    query = select(User)

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    result = await session.execute(query)
    users = result.scalars().all()

    return UsersListResponse(users=users)


@router.get("/{id}", response_model=UserDetailResponse)
async def read_user_by_id(id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with ID {id} not found")

    user_response = UserDetailResponse(
        id=user.id,
        name=user.name,
        username=user.username,
        email=user.email
    )

    return user_response


@router.post("/signup", response_model=UserDetailResponse)
async def create_user(user: SignUpRequest, session: AsyncSession = Depends(get_session)):
    logger.info(f"Received a signup request")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password_hash=hashed_password.decode('utf-8')
    )

    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except RequestValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except IntegrityError:
        await session.rollback()
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


@router.put("/update/{id}", response_model=UserDetailResponse)
async def update_user(id: UUID, user_update: UserUpdateRequest, session: AsyncSession = Depends(get_session)):
    logger.info(f"Received request to update user with ID {id}")
    
    result = await session.execute(select(User).where(User.id == id))
    existing_user = result.scalars().first()

    if not existing_user:
        logger.error(f"User with ID {id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {id} not found")

    if user_update.name is not None:
        existing_user.name = user_update.name
    if user_update.username is not None:
        existing_user.username = user_update.username
    if user_update.email is not None:
        existing_user.email = user_update.email
    if user_update.password is not None:
        hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
        existing_user.password_hash = hashed_password.decode('utf-8')

    try:
        await session.commit()
        await session.refresh(existing_user)
    except IntegrityError:
        await session.rollback()
        logger.warning(f"Username or email already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

    logger.info(f"User with ID {id} updated successfully")
    return UserDetailResponse(
        id=existing_user.id,
        name=existing_user.name,
        username=existing_user.username,
        email=existing_user.email
    )


@router.delete("/delete/{id}")
async def delete_user(id: UUID, session: AsyncSession = Depends(get_session)):
    logger.info(f"Received request to delete user with ID {id}")

    result = await session.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        logger.error(f"User with ID {id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {id} not found")

    await session.delete(user)
    await session.commit()

    logger.info(f"User with ID {id} deleted successfully")
    return {"detail": "User deleted successfully"}
