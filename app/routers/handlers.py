from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.logger import logger
from app.services.exceptions import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    IncorrectPasswordError,
    UnauthorizedError,
    InactiveUserError,
)


async def user_not_found_exception_handler(_: Request, exc: UserNotFoundError):
    logger.error(f"UserNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
        content={"detail": exc.errors()},
    )


async def validation_exception_handler(_: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


async def email_already_exists_exception_handler(
    _: Request, exc: EmailAlreadyExistsError
):
    logger.error(f"UserAlreadyExistsError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


async def username_already_exists_exception_handler(
    _: Request, exc: UsernameAlreadyExistsError
):
    logger.error(f"UserAlreadyExistsError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


async def incorrect_password_exception_handler(_: Request, exc: IncorrectPasswordError):
    logger.error(f"IncorrectPasswordError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


async def unauthorized_exception_handler(_: Request, exc: UnauthorizedError):
    logger.error(f"UnauthorizedError error: {exc.errors()}")
    return JSONResponse(
        status_code=401,
        content={"detail": exc.errors(), "headers": {"WWW-Authenticate": "Bearer"}},
    )


async def inactive_user_exception_handler(_: Request, exc: InactiveUserError):
    logger.error(f"InactiveUserError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )
