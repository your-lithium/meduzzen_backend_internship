import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repo.company import CompanyRepo
from app.schemas.company_schemas import CompanyResponse
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
async def test_create_company(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    response = await client.post("/companies", json=payload.test_company_3.model_dump())
    assert response.status_code == 200
    company = response.json()
    expected_company = {
        **payload.expected_test_company_3,
        "owner_id": (
            await get_user_and_company_ids(
                user_email=payload.test_user_1.email, session=test_session
            )
        )[0],
    }
    assert_real_matches_expected(company, expected_company)


@pytest.mark.asyncio
async def test_get_company_list(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    response = await client.get("/companies")
    assert response.status_code == 200

    companies = response.json()
    assert companies != []

    expected_companies = [
        payload.expected_test_company_1,
        payload.expected_test_company_2,
    ]
    owner_emails = [payload.test_user_1.email, payload.test_user_2.email]
    for company, expected_company, owner_email in zip(
        companies, expected_companies, owner_emails
    ):
        expected_company = {
            **expected_company,
            "owner_id": (
                await get_user_and_company_ids(
                    user_email=owner_email, session=test_session
                )
            )[0],
        }
        assert_real_matches_expected(company, expected_company)


@pytest.mark.asyncio
async def test_get_company_by_id(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    company = await CompanyRepo.get_company_by_name(
        company_name=payload.test_company_1.name, session=test_session
    )
    assert company is not None, "Company not found"
    company_id = company.id
    response = await client.get(f"/companies/{company_id}")
    assert response.status_code == 200
    response_company: CompanyResponse = response.json()
    expected_company = {
        **payload.expected_test_company_1,
        "owner_id": (
            await get_user_and_company_ids(
                user_email=payload.test_user_1.email, session=test_session
            )
        )[0],
    }
    assert_real_matches_expected(response_company, expected_company)


@pytest.mark.asyncio
async def test_update_company(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    company = await CompanyRepo.get_company_by_name(
        company_name=payload.test_company_1.name, session=test_session
    )
    assert company is not None, "Company not found"
    company_id = company.id
    response = await client.patch(
        f"/companies/{company_id}", json=payload.test_company_1_update.model_dump()
    )
    assert response.status_code == 200
    updated_company = response.json()
    expected_company = {
        **payload.expected_test_company_1_update,
        "owner_id": (
            await get_user_and_company_ids(
                user_email=payload.test_user_1.email, session=test_session
            )
        )[0],
    }
    assert_real_matches_expected(updated_company, expected_company)


@pytest.mark.asyncio
async def test_delete_company(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    company = await CompanyRepo.get_company_by_name(
        company_name=payload.test_company_1.name, session=test_session
    )
    assert company is not None, "Company not found"
    company_id = company.id
    await client.delete(f"/companies/{company_id}")
    company = await CompanyRepo.get_by_id(record_id=company_id, session=test_session)
    assert company is None
