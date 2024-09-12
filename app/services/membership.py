from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Company, Membership, StatusEnum, User
from app.db.repo.membership import MembershipRepo
from app.schemas.membership_schemas import MembershipActionRequest
from app.services.company import CompanyService, get_company_service
from app.services.exceptions import (
    AccessDeniedError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
)
from app.services.permissions import PermissionService
from app.services.user import UserService, get_user_service


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
        """Check if parties (Company and User) exist.

        Args:
            parties (MembershipActionRequest): The parties to check.
            session (AsyncSession):
                The database session used for querying users and companies.
                Defaults to the session obtained through get_session.

        Returns:
            tuple[Company, User]: The existing company and user.
        """
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
        """Check if a Company exists and if a User is its owner.

        Args:
            company_id (UUID): The ID of a Company to check.
            current_user (User): The User to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
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
        """Check if parties exist and if the current User is the owner for a Company.

        Args:
            parties (MembershipActionRequest):
                The parties (Company and User) which to check.
            current_user (User): The User who to authorize for ownership.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
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
        """Check if parties exist and if the current User is performing
        operations on their own behalf.

        Args:
            parties (MembershipActionRequest):
                The parties (Company and User) which to check.
            current_user (User): The User who to authorize.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
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
        """Get details for one membership via its ID.

        Args:
            membership_id (UUID): The membership's ID.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipNotFoundError: If there's no Membership with given ID.

        Returns:
            Membership: Membership details.
        """
        membership: Membership | None = await MembershipRepo.get_by_id(
            record_id=membership_id, session=session
        )

        if membership is None:
            raise MembershipNotFoundError(membership_id)

        return membership

    async def get_membership_by_parties(
        self,
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Get details for a membership via its parties.

        Args:
            parties (MembershipActionRequest):
                The parties (Company and User) which to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipNotFoundError:
                If there's no Membership with given parties.

        Returns:
            Membership: Membership details.
        """
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
        """Send an invitation for a User to become a member of a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The current user to authorize as an owner.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User has already rejected membership in the Company.

        Returns:
            Membership: Details of the new invitation.
        """
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
        except MembershipNotFoundError:
            pass
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
        """Cancel an invitation of a User to a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The current user to authorize as an owner.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "invited"
        """
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
            await MembershipRepo.delete(entity=membership, session=session)
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
        """Accept an invitation to join a Company.

        Args:
            company_id (UUID): The company requested.
            current_user (User):
                The current user to authorize and perform an action for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "invited"

        Returns:
            Membership: The accepted invitation.
        """
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
            membership = await MembershipRepo.update_status(
                membership=membership, status=StatusEnum.MEMBER, session=session
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
        """_summary_

        Args:
            company_id (UUID): The company requested.
            current_user (User):
                The current user to authorize and perform an action for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "invited"

        Returns:
            Membership: The declined invitation.
        """
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
            membership = await MembershipRepo.update_status(
                membership=membership,
                status=StatusEnum.DECLINED,
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
        """Send a request to join a Company.

        Args:
            company_id (UUID): The company requested.
            current_user (User):
                The current user to perform an action for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's membership exists and its status is not "declined".

        Returns:
            Membership: The request sent.
        """
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
        except MembershipNotFoundError:
            pass
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
        """Cancel a request to join a Company.

        Args:
            company_id (UUID): The company requested.
            current_user (User):
                The current user to authorize and perform an action for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "requested".
        """
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
            await MembershipRepo.delete(entity=membership, session=session)
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
        """Accept a request to join a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The current user to authorize as an owner.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "requested".

        Returns:
            Membership: The accepted request.
        """
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
            request = await MembershipRepo.update_status(
                membership=membership,
                status=StatusEnum.MEMBER,
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
        """Reject a request to join a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The current user to authorize as an owner.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            MembershipAlreadyExistsError:
                If the User is already a member of the Company.
            AccessDeniedError:
                If the User's status is not "requested".

        Returns:
            Membership: The rejected request.
        """
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
            request = await MembershipRepo.update_status(
                membership=membership,
                status=StatusEnum.REJECTED,
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
        """Terminate a membership.

        Args:
            parties (MembershipActionRequest):
                The parties (User and Company) which to terminate the membership for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            AccessDeniedError: If the User is not a member of the Company.
        """
        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.MEMBER:
            await MembershipRepo.delete(entity=membership, session=session)
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
        """Remove a User as a member from a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The current user to authorize as an owner.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
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
        """Leave a Company as a User.

        Args:
            company_id (UUID): The company requested.
            current_user (User):
                The current user to authorize and perform an action for.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
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
        """Get a User's requests to join Companies.

        Args:
            user_id (UUID): ID of the User to check.
            limit (int, optional): How much requests to get. Defaults to 10.
            offset (int, optional): Where to start getting requests. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a User's requests.
        """
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
        """Get a User's invitations to join Companies.

        Args:
            user_id (UUID): ID of the User to check.
            limit (int, optional): How much invitations to get. Defaults to 10.
            offset (int, optional): Where to start getting invitations. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a User's invitations.
        """
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
        """Get invitations to join a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            current_user (User): The User who to authorize for ownership.
            limit (int, optional): How much invitations to get. Defaults to 10.
            offset (int, optional): Where to start getting invitations. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a Company's invitations.
        """
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
        """Get requests to join a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            current_user (User): The User who to authorize for ownership.
            limit (int, optional): How much requests to get. Defaults to 10.
            offset (int, optional): Where to start getting requests. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a Company's requests.
        """
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
        """Get members of a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            limit (int, optional): How much members to get. Defaults to 10.
            offset (int, optional): Where to start getting members. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The list of a Company's members.
        """
        members = await MembershipRepo.get_members_by_company(
            company_id=company_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return members

    async def get_all_members_by_company(
        self, company_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> list[User]:
        """Get all members of a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The full list of a Company's members.
        """
        limit = 100
        offset = 0
        all_members = []

        while True:
            members = await self.get_members_by_company(
                company_id, limit, offset, session
            )
            if not members:
                break
            all_members.extend(members)
            offset += limit

        return all_members

    async def appoint_admin(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Upgrade a User to an admin of a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The User who to authorize for ownership.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            AccessDeniedError:
                If the User isn't a member of the Company.

        Returns:
            Membership: The upgraded membership.
        """
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
            membership = await MembershipRepo.update_status(
                membership=membership,
                status=StatusEnum.ADMIN,
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

    async def remove_admin(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Downgrade a User from being an admin of a Company.

        Args:
            company_id (UUID): The company requested.
            user_id (UUID): The user requested.
            current_user (User): The User who to authorize for ownership.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            AccessDeniedError:
                If the User isn't a member of the Company.

        Returns:
            Membership: The downgraded membership.
        """
        parties = MembershipActionRequest(company_id=company_id, user_id=user_id)
        await self.check_parties_and_owner(
            parties=parties,
            current_user=current_user,
            session=session,
        )

        membership = await self.get_membership_by_parties(
            parties=parties, session=session
        )
        if membership.status == StatusEnum.ADMIN:
            membership = await MembershipRepo.update_status(
                membership=membership,
                status=StatusEnum.MEMBER,
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

    async def get_admins_by_company(
        self,
        company_id: UUID,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[User]:
        """Get a list of admins in a company.

        Args:
            company_id (UUID): The company which to check.
            limit (int, optional): How much admins to get. Defaults to 10.
            offset (int, optional): Where to start getting admins. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The list of admins.
        """
        admins = await MembershipRepo.get_admins_by_company(
            company_id=company_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return admins
