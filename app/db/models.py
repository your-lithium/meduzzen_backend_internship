import enum

from sqlalchemy import String, Boolean, ForeignKey, Enum, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
from uuid import UUID, uuid4
from pydantic import BaseModel

from app.db.database import Base
from app.schemas.quiz_schemas import Question


class BaseId(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )


class JSONEncodedDict(TypeDecorator):
    impl = JSONB

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, list):
                value = [q.to_dict() if isinstance(q, BaseModel) else q for q in value]
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = [Question.from_dict(q) if isinstance(q, dict) else q for q in value]
        return value


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
    questions: Mapped[list] = mapped_column(JSONEncodedDict, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "jsonb_array_length(questions) >= 2", name="questions_min_length"
        ),
    )
