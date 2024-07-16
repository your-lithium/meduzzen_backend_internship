from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.models import Membership, StatusEnum, User, Company
from app.schemas.membership_schemas import MembershipActionRequest
from app.db.repo.membership import MembershipRepo
from app.services.exceptions import (
    MembershipNotFoundError,
    MembershipAlreadyExistsError,
    AccessDeniedError,
)
from app.db.database import get_session
from app.services.permissions import PermissionService
from app.services.company import get_company_service, CompanyService
from app.services.user import get_user_service, UserService


def get_membership_service(
    user_service=Depends(get_user_service), company_service=Depends(get_company_service)
):
    return MembershipService(user_service, company_service)


class MembershipService:
    """Represents a service for handling requests to Membership model."""

    def __init__(
        self, user_service: UserService, company_service: CompanyService
    ) -> None:
        self._user_service = user_service
        self._company_service = company_service

    async def check_parties(
        self,
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> tuple[Company, User]:
        existing_company = await self._company_service.get_company_by_id(
            company_id=parties.company_id, session=session
        )

        existing_user = await self._user_service.get_user_by_id(
            user_id=parties.user_id,
            session=session,
        )

        return existing_company, existing_user

    async def check_company_and_owner(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        existing_company = await self._company_service.get_company_by_id(
            company_id=company_id, session=session
        )

        PermissionService.grant_owner_permission(
            owner_id=existing_company.owner_id,
            current_user_id=current_user.id,
            operation="update",
        )

    async def check_parties_and_owner(
        self,
        parties: MembershipActionRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        existing_parties = await self.check_parties(
            parties=parties,
            session=session,
        )

        PermissionService.grant_owner_permission(
            owner_id=existing_parties[0].owner_id,
            current_user_id=current_user.id,
            operation="update",
        )

    async def check_parties_and_user(
        self,
        parties: MembershipActionRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        existing_parties = await self.check_parties(
            parties=parties,
            session=session,
        )

        PermissionService.grant_user_permission(
            user_id=existing_parties[1],
            current_user_id=current_user,
            operation="update membership",
        )

    async def get_membership_by_id(
        self,
        membership_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        membership: Membership | None = await MembershipRepo.get_membership_by_id(
            membership_id=membership_id, session=session
        )

        if membership is None:
            raise MembershipNotFoundError(membership_id)

        return membership

    async def get_membership_by_parties(
        self,
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        membership: Membership | None = await MembershipRepo.get_membership_by_parties(
            parties=parties, session=session
        )

        if membership is None:
            raise MembershipNotFoundError(parties)

        return membership

    async def send_invitation(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership: Membership | None = None
        try:
            membership = await self.get_membership_by_parties(
                parties=parties, session=session
            )
        finally:
            if membership:
                if membership.status == StatusEnum.MEMBER:
                    raise MembershipAlreadyExistsError(
                        f"user {parties.user_id} and company {parties.company_id}"
                    )
                elif membership.status != StatusEnum.REJECTED:
                    raise AccessDeniedError(
                        (
                            f"User with ID {parties.user_id} ",
                            f"has membership status {membership.status} ",
                            "that is incompatible with the requested action",
                        )
                    )

            invitation: Membership = await MembershipRepo.send_invitation(
                parties=parties, session=session
            )

            return invitation

    async def cancel_invitation(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.INVITED:
            await MembershipRepo.cancel_invitation(
                membership=membership,
                session=session,
            )
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def accept_invitation(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(company_id=company_id, user_id=current_user)
        await self.check_parties_and_user(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.INVITED:
            membership = await MembershipRepo.accept_invitation(
                membership=membership, session=session
            )
            return membership
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def decline_invitation(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(
            company_id=company_id, user_id=current_user.id
        )
        await self.check_parties_and_user(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.INVITED:
            membership = await MembershipRepo.decline_invitation(
                membership=membership,
                session=session,
            )
            return membership
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def send_request(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(
            company_id=company_id, user_id=current_user.id
        )
        await self.check_parties_and_user(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership: Membership | None = None
        try:
            membership = await self.get_membership_by_parties(
                parties=parties, session=session
            )
        finally:
            if membership:
                if membership.status == StatusEnum.MEMBER:
                    raise MembershipAlreadyExistsError(
                        f"user {parties.user_id} and company {parties.company_id}"
                    )
                elif membership.status != StatusEnum.DECLINED:
                    raise AccessDeniedError(
                        (
                            f"User with ID {parties.user_id} ",
                            f"has membership status {membership.status} ",
                            "that is incompatible with the requested action",
                        )
                    )

            request = await MembershipRepo.send_request(
                parties=parties,
                session=session,
            )

            return request

    async def cancel_request(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        parties = MembershipActionRequest(
            company_id=company_id, user_id=current_user.id
        )
        await self.check_parties_and_user(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.REQUESTED:
            await MembershipRepo.cancel_request(
                membership=membership,
                session=session,
            )
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def accept_request(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.REQUESTED:
            request = await MembershipRepo.accept_request(
                membership=membership,
                session=session,
            )
            return request
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def reject_request(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            raise MembershipAlreadyExistsError(
                f"user {parties.user_id} and company {parties.company_id}"
            )
        elif membership.status == StatusEnum.REQUESTED:
            request = await MembershipRepo.reject_request(
                membership=membership,
                session=session,
            )
            return request
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def terminate_membership(
        self,
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            await MembershipRepo.terminate_membership(
                membership=membership, session=session
            )
        else:
            raise AccessDeniedError(
                (
                    f"User with ID {parties.user_id} ",
                    f"has membership status {membership.status} ",
                    "that is incompatible with the requested action",
                )
            )

    async def remove_member(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        await self.terminate_membership(
            parties=parties,
            session=session,
        )

    async def leave_company(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        parties = MembershipActionRequest(
            company_id=company_id, user_id=current_user.id
        )
        await self.check_parties_and_user(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        await self.terminate_membership(
            parties=parties,
            session=session,
        )

    async def get_requests_by_user(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        requests = await MembershipRepo.get_requests_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return requests

    async def get_invitations_by_user(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        invitations = await MembershipRepo.get_invitations_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return invitations

    async def get_invitations_by_company(
        self,
        company_id: UUID,
        current_user: User,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        await self.check_company_and_owner(
            company_id=company_id,
            current_user=current_user,
            session=session,
        )

        invitations = await MembershipRepo.get_invitations_by_company(
            company_id=company_id, limit=limit, offset=offset, session=session
        )
        return invitations

    async def get_requests_by_company(
        self,
        company_id: UUID,
        current_user: User,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        await self.check_company_and_owner(
            company_id=company_id,
            current_user=current_user,
            session=session,
        )

        requests = await MembershipRepo.get_requests_by_company(
            company_id=company_id, limit=limit, offset=offset, session=session
        )
        return requests

    async def get_members_by_company(
        self,
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[User]:
        members = await MembershipRepo.get_members_by_company(
            company_id=company_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return members
