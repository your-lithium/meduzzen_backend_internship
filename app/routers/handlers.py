from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.services.exceptions import (
    UserNotFoundError,
    CompanyNotFoundError,
    MembershipNotFoundError,
    QuizNotFoundError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    CompanyNameAlreadyExistsError,
    MembershipAlreadyExistsError,
    IncorrectPasswordError,
    UnauthorizedError,
    InactiveUserError,
    AccessDeniedError,
)


async def user_not_found_exception_handler(_: Request, exc: UserNotFoundError):
    logger.error(f"UserNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
        content={"detail": exc.errors()},
    )


async def company_not_found_exception_handler(_: Request, exc: CompanyNotFoundError):
    logger.error(f"CompanyNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
        content={"detail": exc.errors()},
    )


async def membership_not_found_exception_handler(
    _: Request, exc: MembershipNotFoundError
):
    logger.error(f"MembershipNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
        content={"detail": exc.errors()},
    )


async def quiz_not_found_exception_handler(_: Request, exc: QuizNotFoundError):
    logger.error(f"QuizNotFoundError error: {exc.errors()}")
    return JSONResponse(
        status_code=404,
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


async def company_name_already_exists_exception_handler(
    _: Request, exc: CompanyNameAlreadyExistsError
):
    logger.error(f"CompanyNameAlreadyExistsError error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


async def membership_already_exists_exception_handler(
    _: Request, exc: MembershipAlreadyExistsError
):
    logger.error(f"MembershipAlreadyExistsError error: {exc.errors()}")
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


async def access_denied_exception_handler(_: Request, exc: AccessDeniedError):
    logger.error(f"AccessDeniedError error: {exc.errors()}")
    return JSONResponse(
        status_code=403,
        content={"detail": exc.errors()},
    )
