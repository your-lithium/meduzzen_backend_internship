from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql
from uuid import UUID, uuid4
import enum

from app.db.database import Base


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
    INVITED = "invite"
    DECLINED = "declined"  # can't be invited again, but can request membership
    REQUESTED = "request"
    REJECTED = "rejected"  # can't request membership again, but can be invited


class Membership(BaseId):
    __tablename__ = "membership"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("company.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False)
