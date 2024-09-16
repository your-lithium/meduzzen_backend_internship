import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repo.user import UserRepo
from app.schemas.user_schemas import UserDetailResponse
from tests import payload


def assert_user_matches_expected(user: dict, expected: dict):
    for key, value in expected.items():
        assert user[key] == value


@pytest.mark.asyncio
async def test_create_user(fill_db_with_users, client: AsyncClient):
    response = await client.post("/auth/signup", json=payload.test_user_3.model_dump())
    assert response.status_code == 200
    user = response.json()
    assert_user_matches_expected(user, payload.expected_test_user_3)


@pytest.mark.asyncio
async def test_get_user_list(fill_db_with_users, client: AsyncClient):
    response = await client.get("/users")
    assert response.status_code == 200

    users = response.json()
    expected_values = [payload.expected_test_user_1, payload.expected_test_user_2]
    for i, user in enumerate(users):
        assert_user_matches_expected(user, expected_values[i])


@pytest.mark.asyncio
async def test_get_user_by_id(
    fill_db_with_users, client: AsyncClient, test_session: AsyncSession
):
    user = await UserRepo.get_user_by_email(
        user_email=payload.test_user_1.email, session=test_session
    )
    assert user is not None, "User not found"
    user_id = user.id
    response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    response_user: UserDetailResponse = response.json()
    assert_user_matches_expected(response_user, payload.expected_test_user_1)
    assert "password_hash" not in response_user


@pytest.mark.asyncio
async def test_update_user(
    fill_db_with_users, client: AsyncClient, test_session: AsyncSession
):
    user = await UserRepo.get_user_by_email(
        user_email=payload.test_user_1.email, session=test_session
    )
    assert user is not None, "User not found"
    user_id = user.id
    response = await client.patch(
        f"/users/{user_id}", json=payload.test_user_1_update.model_dump()
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert_user_matches_expected(updated_user, payload.expected_test_user_1_update)
    assert "password_hash" not in updated_user


@pytest.mark.asyncio
async def test_delete_user(
    fill_db_with_users, client: AsyncClient, test_session: AsyncSession
):
    user = await UserRepo.get_user_by_email(
        user_email=payload.test_user_1.email, session=test_session
    )
    assert user is not None, "User not found"
    user_id = user.id
    await client.delete(f"/users/{user_id}")
    user = await UserRepo.get_by_id(record_id=user_id, session=test_session)
    assert user is None
