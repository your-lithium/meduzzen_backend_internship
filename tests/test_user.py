import pytest
import asyncio
import pytest_asyncio
import bcrypt
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.database import Base, get_session
from app.db.user_model import User
from app.main import app
from app.core.config import config
from tests import payload


test_engine = create_async_engine(config.postgres_test_url, echo=True, future=True)


@pytest_asyncio.fixture
async def test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def setup_and_teardown_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    users = [payload.test_user_1.model_dump(), payload.test_user_2.model_dump()]
    for user in users:
        hashed_password = bcrypt.hashpw(
            user["password"].encode("utf-8"), bcrypt.gensalt()
        )
        user["password_hash"] = hashed_password.decode("utf-8")
        del user["password"]

    async for session in override_get_session():
        try:
            async with session as db_session:
                await db_session.execute(insert(User).values(users))
                await db_session.commit()

            yield

        finally:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)


async def override_get_session() -> AsyncSession:
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.mark.asyncio
async def test_create_user(test_client, setup_and_teardown_db):
    response = await test_client.post(
        "/auth/signup", json=payload.test_user_3.model_dump()
    )
    assert response.status_code == 200
    user_1 = response.json()
    assert user_1 == payload.expected_test_user_3


@pytest.mark.asyncio
async def test_get_user_list(test_client, setup_and_teardown_db):
    response = await test_client.get("/users")
    assert response.status_code == 200

    users = response.json()
    expected_values = [payload.expected_test_user_1, payload.expected_test_user_2]
    for i, user in enumerate(users):
        assert "password_hash" in user
        del user["password_hash"]
        assert user == expected_values[i]


@pytest.mark.asyncio
async def test_get_user_by_id(test_client, setup_and_teardown_db):
    assert asyncio.get_running_loop()
    user_id = payload.test_user_1.id
    response = await test_client.get(f"/users/{user_id}")
    assert response.status_code == 200
    user_1 = response.json()
    assert user_1 == payload.expected_test_user_1
    assert "password_hash" not in user_1


@pytest.mark.asyncio
async def test_update_user(test_client, setup_and_teardown_db):
    user_id = payload.test_user_1.id
    response = await test_client.patch(
        f"/users/{user_id}", json=payload.test_user_1_update.model_dump()
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user == payload.expected_test_user_1_update
    assert "password_hash" not in updated_user


@pytest.mark.asyncio
async def test_delete_user(test_client, setup_and_teardown_db):
    user_1_id = payload.test_user_1.id
    await test_client.delete(f"/users/{user_1_id}")
    user_2_id = payload.test_user_2.id
    await test_client.delete(f"/users/{user_2_id}")
    response = await test_client.get("/users")
    assert response.status_code == 200
    assert response.json() == []
