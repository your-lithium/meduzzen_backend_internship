import pytest
import pytest_asyncio
import bcrypt
from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import config
from app.db.database import Base, get_session
from app.db.models import User
from app.main import app
from tests import payload


@pytest_asyncio.fixture(scope="session")
async def prepare_db():
    create_async_engine(
        config.postgres_test_url, echo=True, future=True, isolation_level="AUTOCOMMIT"
    )


@pytest.fixture(scope="function")
def engine():
    engine = create_async_engine(config.postgres_test_url)
    yield engine
    engine.sync_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(prepare_db, engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
        class_=AsyncSession,
    )

    async with TestingSessionLocal() as test_session:
        yield test_session
        await test_session.flush()
        await test_session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def override_get_session(test_session):
    async def _override_get_session():
        yield test_session

    return _override_get_session


@pytest_asyncio.fixture(scope="function")
async def client(override_get_session):
    app.dependency_overrides[get_session] = override_get_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def fill_db_with_users(test_session: AsyncSession):
    users = [payload.test_user_1.model_dump(), payload.test_user_2.model_dump()]

    for user in users:
        hashed_password = bcrypt.hashpw(
            user["password"].encode("utf-8"), bcrypt.gensalt()
        )
        user["password_hash"] = hashed_password.decode("utf-8")
        user.pop("password")

        db_user = User(**user)
        test_session.add(db_user)

        await test_session.commit()
