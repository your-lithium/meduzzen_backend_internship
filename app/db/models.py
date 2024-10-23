import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.schemas.quiz_schemas import QuestionList


class BaseId(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )


class User(BaseId):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=False)
    username: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Company(BaseId):
    __tablename__ = "company"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StatusEnum(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"
    INVITED = "invited"
    DECLINED = "declined"  # can't be invited again, but can request membership
    REQUESTED = "requested"
    REJECTED = "rejected"  # can't request membership again, but can be invited


class Membership(BaseId):
    __tablename__ = "membership"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("company.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False)


class Quiz(BaseId):
    __tablename__ = "quiz"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("company.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    questions: Mapped[QuestionList] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "jsonb_array_length(questions) >= 2", name="questions_min_length"
        ),
    )


class QuizResult(BaseId):
    __tablename__ = "quiz_result"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("company.id"), nullable=False)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quiz.id"), nullable=False)
    time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    answered: Mapped[int] = mapped_column(Integer, nullable=False)
    correct: Mapped[int] = mapped_column(Integer, nullable=False)


class NotificationStatusEnum(enum.Enum):
    READ = "read"
    UNREAD = "unread"


class Notification(BaseId):
    __tablename__ = "notification"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    status: Mapped[NotificationStatusEnum] = mapped_column(
        Enum(NotificationStatusEnum), nullable=False
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
