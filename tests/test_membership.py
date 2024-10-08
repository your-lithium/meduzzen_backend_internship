import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StatusEnum
from app.db.repo.membership import MembershipRepo
from app.schemas.membership_schemas import MembershipActionRequest
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
async def test_send_invitation(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.post(f"/memberships/{company_id}/invitation/{user_id}")
    assert response.status_code == 200
    membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.INVITED.value,
    }
    assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.INVITED], indirect=True
)
async def test_cancel_invitation(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await client.delete(f"/memberships/{company_id}/invitation/{user_id}")
    membership = await MembershipRepo.get_membership_by_parties(
        parties=parties, session=test_session
    )
    assert membership is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.INVITED], indirect=True
)
async def test_accept_invitation(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/invitation/me/accept",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.MEMBER.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.INVITED], indirect=True
)
async def test_decline_invitation(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/invitation/me/decline",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.DECLINED.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
async def test_send_request(
    fill_db_with_companies, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    response = await client.post(f"/memberships/{company_id}/request")
    assert response.status_code == 200
    membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.REQUESTED.value,
    }
    assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.REQUESTED], indirect=True
)
async def test_cancel_request(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await client.delete(f"/memberships/{company_id}/request")
    membership = await MembershipRepo.get_membership_by_parties(
        parties=parties, session=test_session
    )
    assert membership is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.REQUESTED], indirect=True
)
async def test_accept_request(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/request/{user_id}/accept",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.MEMBER.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.REQUESTED], indirect=True
)
async def test_reject_request(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/request/{user_id}/decline",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.REJECTED.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_remove_member(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await client.delete(f"/memberships/{company_id}/remove/{user_id}")
    membership = await MembershipRepo.get_membership_by_parties(
        parties=parties, session=test_session
    )
    assert membership is None


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_leave_company(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await client.delete(f"/memberships/{company_id}/leave")
    membership = await MembershipRepo.get_membership_by_parties(
        parties=parties, session=test_session
    )
    assert membership is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.REQUESTED], indirect=True
)
async def test_get_current_users_requests(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    response = await client.get("/memberships/me/requests")
    assert response.status_code == 200

    memberships = response.json()
    assert memberships != []

    expected_memberships = [
        {
            "company_id": company_id,
            "user_id": user_id,
            "status": StatusEnum.REQUESTED.value,
        }
    ]
    for membership, expected_membership in zip(memberships, expected_memberships):
        assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.INVITED], indirect=True
)
async def test_get_current_users_invitations(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    response = await client.get("/memberships/me/invitations")
    assert response.status_code == 200

    memberships = response.json()
    assert memberships != []

    expected_memberships = [
        {
            "company_id": company_id,
            "user_id": user_id,
            "status": StatusEnum.INVITED.value,
        }
    ]
    for membership, expected_membership in zip(memberships, expected_memberships):
        assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.INVITED], indirect=True
)
async def test_get_invitations_by_company(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/memberships/{company_id}/invitations")
    assert response.status_code == 200

    memberships = response.json()
    assert memberships != []

    expected_memberships = [
        {
            "company_id": company_id,
            "user_id": user_id,
            "status": StatusEnum.INVITED.value,
        }
    ]
    for membership, expected_membership in zip(memberships, expected_memberships):
        assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fill_db_with_memberships", [StatusEnum.REQUESTED], indirect=True
)
async def test_get_requests_by_company(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/memberships/{company_id}/requests")
    assert response.status_code == 200

    memberships = response.json()
    assert memberships != []

    expected_memberships = [
        {
            "company_id": company_id,
            "user_id": user_id,
            "status": StatusEnum.REQUESTED.value,
        }
    ]
    for membership, expected_membership in zip(memberships, expected_memberships):
        assert_real_matches_expected(membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_members_by_company(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/memberships/{company_id}/members")
    assert response.status_code == 200

    members = response.json()
    assert members != []

    expected_members = [payload.expected_test_user_2]
    for member, expected_member in zip(members, expected_members):
        assert_real_matches_expected(member, expected_member)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_appoint_admin(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/admins/{user_id}/appoint",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.ADMIN.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.ADMIN], indirect=True)
async def test_remove_admin(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.patch(
        f"/memberships/{company_id}/admins/{user_id}/remove",
        json=payload.test_company_1_update.model_dump(),
    )
    assert response.status_code == 200
    updated_membership = response.json()
    expected_membership = {
        "company_id": company_id,
        "user_id": user_id,
        "status": StatusEnum.MEMBER.value,
    }
    assert_real_matches_expected(updated_membership, expected_membership)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.ADMIN], indirect=True)
async def test_get_admins_by_company(
    fill_db_with_memberships, client: AsyncClient, test_session: AsyncSession
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/memberships/{company_id}/admins")
    assert response.status_code == 200

    admins = response.json()
    assert admins != []

    expected_admins = [payload.expected_test_user_2]
    for admin, expected_admin in zip(admins, expected_admins):
        assert_real_matches_expected(admin, expected_admin)
