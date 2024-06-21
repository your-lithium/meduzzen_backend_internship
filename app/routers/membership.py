from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.membership_schemas import (
    MembershipResponse,
    MembershipActionRequest,
)
from app.schemas.user_schemas import UserResponse
from app.services.user import get_user_service
from app.services.company import get_company_service
from app.services.membership import get_membership_service
from app.db.database import get_session
from app.db.models import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/memberships")


@router.post("/invitations/{company_id}/{user_id}", response_model=MembershipResponse)
async def send_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    invitation = await membership_service.send_invitation(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return invitation


@router.delete(
    "/invitations/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await membership_service.cancel_invitation(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )


@router.patch(
    "/invitations/{company_id}/{user_id}/accept", response_model=MembershipResponse
)
async def accept_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    membership = await membership_service.accept_invitation(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return membership


@router.patch(
    "/invitations/{company_id}/{user_id}/decline", response_model=MembershipResponse
)
async def decline_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    membership = await membership_service.decline_invitation(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return membership


@router.post("/requests/{company_id}/{user_id}", response_model=MembershipResponse)
async def send_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    request = await membership_service.send_request(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return request


@router.delete(
    "/requests/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await membership_service.cancel_request(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )


@router.patch(
    "/requests/{company_id}/{user_id}/accept", response_model=MembershipResponse
)
async def accept_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    membership = await membership_service.accept_request(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return membership


@router.patch(
    "/requests/{company_id}/{user_id}/decline", response_model=MembershipResponse
)
async def decline_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    membership = await membership_service.decline_request(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )

    return membership


@router.delete("/owner/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await membership_service.remove_member(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )


@router.delete("/user/{user_id}/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_company(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    user_service=Depends(get_user_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
    await membership_service.leave_company(
        parties=parties,
        current_user=current_user,
        company_service=company_service,
        user_service=user_service,
        session=session,
    )


@router.get("/user/{user_id}/requests", response_model=list[MembershipResponse])
async def get_requests_by_user(
    user_id: UUID,
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    requests = await membership_service.get_requests_by_user(
        user_id=user_id, limit=limit, offset=offset, session=session
    )
    return requests


@router.get("/user/{user_id}/invitations", response_model=list[MembershipResponse])
async def get_invitations_by_user(
    user_id: UUID,
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    invitations = await membership_service.get_invitations_by_user(
        user_id=user_id, limit=limit, offset=offset, session=session
    )
    return invitations


@router.get("/owner/{company_id}/invitations", response_model=list[MembershipResponse])
async def get_invitations_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    invitations = await membership_service.get_invitations_by_company(
        company_id=company_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
        company_service=company_service,
        session=session,
    )
    return invitations


@router.get("/owner/{company_id}/requests", response_model=list[MembershipResponse])
async def get_requests_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    company_service=Depends(get_company_service),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    requests = await membership_service.get_requests_by_company(
        company_id=company_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
        company_service=company_service,
        session=session,
    )
    return requests


@router.get("/{company_id}/users", response_model=list[UserResponse])
async def get_members_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    print(company_id)
    print(type(company_id))
    members = await membership_service.get_members_by_company(
        company_id=company_id,
        limit=limit,
        offset=offset,
        session=session,
    )
    return members
