from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import ValidationError

from app.routers import health_check, user, auth
from app.core.config import config
from app.routers.handlers import (
    validation_exception_handler,
    user_not_found_exception_handler,
    email_already_exists_exception_handler,
    username_already_exists_exception_handler,
    incorrect_password_exception_handler,
    unauthorized_exception_handler,
    inactive_user_exception_handler,
)
from app.services.exceptions import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    IncorrectPasswordError,
    UnauthorizedError,
    InactiveUserError,
)


app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_check.router)
app.include_router(user.router)
app.include_router(auth.router)

app.add_exception_handler(UserNotFoundError, user_not_found_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(
    EmailAlreadyExistsError, email_already_exists_exception_handler
)
app.add_exception_handler(
    UsernameAlreadyExistsError, username_already_exists_exception_handler
)
app.add_exception_handler(IncorrectPasswordError, incorrect_password_exception_handler)
app.add_exception_handler(UnauthorizedError, unauthorized_exception_handler)
app.add_exception_handler(InactiveUserError, inactive_user_exception_handler)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.host, port=config.port, reload=True)
