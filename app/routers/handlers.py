from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.services.exceptions import UserNotFoundError, EmailAlreadyExistsError, UsernameAlreadyExistsError


async def user_not_found_exception_handler(_: Request, exc: UserNotFoundError):
    logger.error(f"UserNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.errors()
        },
    )


async def email_already_exists_exception_handler(_: Request, exc: EmailAlreadyExistsError):
    logger.error(f"UserAlreadyExistsError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.errors()
        },
    )


async def username_already_exists_exception_handler(_: Request, exc: UsernameAlreadyExistsError):
    logger.error(f"UserAlreadyExistsError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.errors()
        },
    )