from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ABC(Base):
    __abstract__ = True
    uid = mapped_column(Integer, primary_key=True, autoincrement=True)


class User(ABC):
    __tablename__ = 'user'

    name: Mapped[str] = mapped_column(String, nullable=False, unique=False)
    username: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
