import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.database import Base, get_session
from app.main import app
from app.core.config import config
from tests.payload import (
    test_user_1,
    expected_test_user_1,
    test_user_2,
    expected_test_user_2,
    test_user_1_update,
    expected_test_user_1_update,
)


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

    yield

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
async def test_get_empty_user_list(test_client, setup_and_teardown_db):
    response = await test_client.get("/users")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_user(test_client, setup_and_teardown_db):
    response = await test_client.post("/auth/signup", json=test_user_1.model_dump())
    assert response.status_code == 200
    user_1 = response.json()
    assert all(
        user_1[key] == expected_test_user_1[key] for key in expected_test_user_1.keys()
    )


@pytest.mark.asyncio
async def test_get_user_list(test_client, setup_and_teardown_db):
    await test_client.post("/auth/signup", json=test_user_1.model_dump())
    await test_client.post("/auth/signup", json=test_user_2.model_dump())
    response = await test_client.get("/users")
    assert response.status_code == 200

    user_1 = response.json()[0]
    user_2 = response.json()[1]

    keys_to_check = ["id", "password_hash"]

    for user in [user_1, user_2]:
        assert all(key in user for key in keys_to_check)

    assert all(
        user_1[key] == expected_test_user_1[key] for key in expected_test_user_1.keys()
    )
    assert all(
        user_2[key] == expected_test_user_2[key] for key in expected_test_user_2.keys()
    )


@pytest.mark.asyncio
async def test_get_user_by_id(test_client, setup_and_teardown_db):
    user = await test_client.post("/auth/signup", json=test_user_1.model_dump())
    user_id = user.json()["id"]
    response = await test_client.get(f"/users/{user_id}")
    assert response.status_code == 200
    user_1 = response.json()
    assert all(
        user_1[key] == expected_test_user_1[key] for key in expected_test_user_1.keys()
    )


@pytest.mark.asyncio
async def test_update_user(test_client, setup_and_teardown_db):
    existing_user = await test_client.post(
        "/auth/signup", json=test_user_1.model_dump()
    )
    user_id = existing_user.json()["id"]
    response = await test_client.patch(
        f"/users/{user_id}", json=test_user_1_update.model_dump()
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert all(
        updated_user[key] == expected_test_user_1_update[key]
        for key in expected_test_user_1_update.keys()
    )
    assert "password_hash" not in updated_user


@pytest.mark.asyncio
async def test_delete_user(test_client, setup_and_teardown_db):
    existing_user = await test_client.post(
        "/auth/signup", json=test_user_2.model_dump()
    )
    user_id = existing_user.json()["id"]
    await test_client.delete(f"/users/{user_id}")
    response = await test_client.get("/users")
    assert response.status_code == 200
    assert response.json() == []
