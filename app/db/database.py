from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

from app.core.config import config
from app.core.logger import logger

engine = create_async_engine(config.postgres_url, echo=True, future=True)
Base = declarative_base()


async def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def check_database_exists(conn):
    tables = await conn.run_sync(
        lambda sync_conn: inspect(sync_conn).get_table_names()
    )
    return tables


async def create_db():
    async with engine.begin() as conn:
        existing_tables = await check_database_exists(conn)
        if not existing_tables:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database created successfully.")
        else:
            logger.info("Database already exists.")
