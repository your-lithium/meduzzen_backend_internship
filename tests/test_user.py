import pytest
import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.database import Base, get_session
from app.main import app
from app.core.config import config
from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest

config.postgres_name += "_test"
config.update_postgres_url()
test_engine = create_async_engine(config.postgres_url, echo=True, future=True)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_and_teardown_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def override_get_session() -> AsyncSession:
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


test_user_1 = SignUpRequest(
    name="test user 1",
    username="test1",
    email="test1@test.com",
    password="testpassword1",
)
test_user_2 = SignUpRequest(
    name="test user 2",
    username="test2",
    email="test2@test.com",
    password="testpassword2",
)
test_user_1_update = UserUpdateRequest(
    name="updated test user 1", password="updatedtestpassword1"
)


@pytest.mark.asyncio
async def test_get_empty_user_list():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/signup", json=test_user_1.model_dump())
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == test_user_1.name
    assert response_data["username"] == test_user_1.username
    assert response_data["email"] == test_user_1.email


@pytest.mark.asyncio
async def test_get_user_list():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/auth/signup", json=test_user_1.model_dump())
        await client.post("/auth/signup", json=test_user_2.model_dump())
        response = await client.get("/users")
    assert response.status_code == 200

    user_1 = response.json()[0]
    user_2 = response.json()[1]

    assert "id" in user_1
    assert "id" in user_2
    assert "password_hash" in user_1
    assert "password_hash" in user_2

    assert user_1["name"] == "test user 1"
    assert user_1["username"] == "test1"
    assert user_1["email"] == "test1@test.com"

    assert user_2["name"] == "test user 2"
    assert user_2["username"] == "test2"
    assert user_2["email"] == "test2@test.com"


@pytest.mark.asyncio
async def test_get_user_by_id():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        user = await client.post("/auth/signup", json=test_user_1.model_dump())
        user_id = user.json()["id"]
        response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == test_user_1.name
    assert response_data["username"] == test_user_1.username
    assert response_data["email"] == test_user_1.email


@pytest.mark.asyncio
async def test_update_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        existing_user = await client.post("/auth/signup", json=test_user_1.model_dump())
        user_id = existing_user.json()["id"]
        updated_user = await client.patch(
            f"/users/{user_id}", json=test_user_1_update.model_dump()
        )
    assert updated_user.status_code == 200
    existing_user_data = existing_user.json()
    updated_user_data = updated_user.json()
    assert updated_user_data["name"] == test_user_1_update.name
    assert updated_user_data["username"] == existing_user_data["username"]
    assert updated_user_data["email"] == existing_user_data["email"]
    assert "password_hash" not in updated_user_data


@pytest.mark.asyncio
async def test_delete_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        existing_user = await client.post("/auth/signup", json=test_user_2.model_dump())
        user_id = existing_user.json()["id"]
        await client.delete(f"/users/{user_id}")
        response = await client.get("/users")
    assert response.status_code == 200
    assert response.json() == []
