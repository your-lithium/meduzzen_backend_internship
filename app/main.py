from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.routers import (
    analytics,
    auth,
    company,
    health_check,
    membership,
    notification,
    quiz,
    user,
)
from app.routers.handlers import (
    access_denied_exception_handler,
    company_name_already_exists_exception_handler,
    company_not_found_exception_handler,
    email_already_exists_exception_handler,
    inactive_user_exception_handler,
    incomplete_quiz_exception_handler,
    incorrect_password_exception_handler,
    membership_already_exists_exception_handler,
    membership_not_found_exception_handler,
    notification_not_found_exception_handler,
    quiz_not_found_exception_handler,
    results_not_found_exception_handler,
    unauthorized_exception_handler,
    unsupported_file_format_exception_handler,
    user_not_found_exception_handler,
    username_already_exists_exception_handler,
)
from app.services.exceptions import (
    AccessDeniedError,
    CompanyNameAlreadyExistsError,
    CompanyNotFoundError,
    EmailAlreadyExistsError,
    InactiveUserError,
    IncompleteQuizError,
    IncorrectPasswordError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    NotificationNotFoundError,
    QuizNotFoundError,
    ResultsNotFoundError,
    UnauthorizedError,
    UnsupportedFileFormatError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from app.utils.apscheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

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
app.include_router(company.router)
app.include_router(membership.router)
app.include_router(quiz.router)
app.include_router(analytics.router)
app.include_router(notification.router)

app.add_exception_handler(UserNotFoundError, user_not_found_exception_handler)
app.add_exception_handler(CompanyNotFoundError, company_not_found_exception_handler)
app.add_exception_handler(
    MembershipNotFoundError, membership_not_found_exception_handler
)
app.add_exception_handler(QuizNotFoundError, quiz_not_found_exception_handler)
app.add_exception_handler(ResultsNotFoundError, results_not_found_exception_handler)
app.add_exception_handler(
    NotificationNotFoundError, notification_not_found_exception_handler
)
app.add_exception_handler(
    EmailAlreadyExistsError, email_already_exists_exception_handler
)
app.add_exception_handler(
    UsernameAlreadyExistsError, username_already_exists_exception_handler
)
app.add_exception_handler(
    CompanyNameAlreadyExistsError, company_name_already_exists_exception_handler
)
app.add_exception_handler(
    MembershipAlreadyExistsError, membership_already_exists_exception_handler
)
app.add_exception_handler(IncorrectPasswordError, incorrect_password_exception_handler)
app.add_exception_handler(UnauthorizedError, unauthorized_exception_handler)
app.add_exception_handler(InactiveUserError, inactive_user_exception_handler)
app.add_exception_handler(AccessDeniedError, access_denied_exception_handler)
app.add_exception_handler(IncompleteQuizError, incomplete_quiz_exception_handler)
app.add_exception_handler(
    UnsupportedFileFormatError, unsupported_file_format_exception_handler
)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.host, port=config.port, reload=True)
