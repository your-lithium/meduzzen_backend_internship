from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.membership_schemas import MembershipResponse
from app.schemas.user_schemas import UserResponse
from app.services.membership import get_membership_service
from app.db.database import get_session
from app.db.models import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/memberships")


@router.post("/{company_id}/invitation/{user_id}", response_model=MembershipResponse)
async def send_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    invitation = await membership_service.send_invitation(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )

    return invitation


@router.delete(
    "/{company_id}/invitation/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_invitation(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    await membership_service.cancel_invitation(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )


@router.patch(
    "/{company_id}/invitation/{user_id}/accept", response_model=MembershipResponse
)
async def accept_invitation(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.accept_invitation(
        company_id=company_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.patch(
    "/{company_id}/invitation/{user_id}/decline", response_model=MembershipResponse
)
async def decline_invitation(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.decline_invitation(
        company_id=company_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.post("/{company_id}/request", response_model=MembershipResponse)
async def send_request(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    request = await membership_service.send_request(
        company_id=company_id,
        current_user=current_user,
        session=session,
    )

    return request


@router.delete("/{company_id}/request", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_request(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    await membership_service.cancel_request(
        company_id=company_id,
        current_user=current_user,
        session=session,
    )


@router.patch(
    "/{company_id}/request/{user_id}/accept", response_model=MembershipResponse
)
async def accept_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.accept_request(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.patch(
    "/{company_id}/request/{user_id}/decline", response_model=MembershipResponse
)
async def reject_request(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.decline_request(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.delete("/{company_id}/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    await membership_service.remove_member(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )


@router.delete("/{company_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    await membership_service.leave_company(
        company_id=company_id,
        current_user=current_user,
        session=session,
    )


@router.get("/me/requests", response_model=list[MembershipResponse])
async def get_current_users_requests(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    requests = await membership_service.get_requests_by_user(
        user_id=current_user.id, limit=limit, offset=offset, session=session
    )
    return requests


@router.get("/me/invitations", response_model=list[MembershipResponse])
async def get_current_users_invitations(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    invitations = await membership_service.get_invitations_by_user(
        user_id=current_user.id, limit=limit, offset=offset, session=session
    )
    return invitations


@router.get("/{company_id}/invitations", response_model=list[MembershipResponse])
async def get_invitations_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    invitations = await membership_service.get_invitations_by_company(
        company_id=company_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
        session=session,
    )
    return invitations


@router.get("/{company_id}/requests", response_model=list[MembershipResponse])
async def get_requests_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    requests = await membership_service.get_requests_by_company(
        company_id=company_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
        session=session,
    )
    return requests


@router.get("/{company_id}/members", response_model=list[UserResponse])
async def get_members_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    members = await membership_service.get_members_by_company(
        company_id=company_id,
        limit=limit,
        offset=offset,
        session=session,
    )
    return members


@router.patch(
    "/{company_id}/admins/{user_id}/appoint", response_model=MembershipResponse
)
async def appoint_admin(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.appoint_admin(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.patch(
    "/{company_id}/admins/{user_id}/remove", response_model=MembershipResponse
)
async def remove_admin(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    membership = await membership_service.remove_admin(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )

    return membership


@router.get("/{company_id}/admins", response_model=list[UserResponse])
async def get_admins_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    membership_service=Depends(get_membership_service),
    session: AsyncSession = Depends(get_session),
):
    admins = await membership_service.get_admins_by_company(
        company_id=company_id,
        limit=limit,
        offset=offset,
        session=session,
    )
    return admins
