from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql
from uuid import UUID, uuid4

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
