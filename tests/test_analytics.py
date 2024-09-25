import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StatusEnum
from tests import payload
from tests.conftest import get_user_and_company_ids


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_user_company_rating(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/analytics/{user_id}/rating/{company_id}")
    assert response.status_code == 200
    rating = response.json()
    assert rating == payload.expected_test_user_2_rating


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_user_rating(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, _ = await get_user_and_company_ids(
        user_email=payload.test_user_1.email, session=test_session
    )
    response = await client.get(f"/analytics/{user_id}/rating")
    print(response.json())
    assert response.status_code == 200
    rating = response.json()
    assert rating == payload.expected_test_user_1_rating
