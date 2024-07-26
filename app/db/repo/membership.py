from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import and_

from app.core.logger import logger
from app.db.database import get_session
from app.db.models import Membership, StatusEnum, User
from app.schemas.membership_schemas import MembershipActionRequest


class MembershipRepo:
    """Represents a repository pattern to perform CRUD on Membership model."""

    @staticmethod
    def get_common_where_clause(
        status: StatusEnum, user_id: UUID | None = None, company_id: UUID | None = None
    ):
        if user_id:
            return and_(
                Membership.user_id == user_id,
                Membership.status == status,
            )
        elif company_id:
            return and_(
                Membership.company_id == company_id,
                Membership.status == status,
            )

    @staticmethod
    async def get_membership_by_id(
        membership_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Membership | None:
        """Get details for one membership via its ID.

        Args:
            membership_id (UUID): The membership's ID.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership | None: Membership details.
        """
        result = await session.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalars().first()

        return membership

    @staticmethod
    async def get_membership_by_parties(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership | None:
        """Get details for a membership via its parties.

        Args:
            parties (MembershipActionRequest):
                The parties (Company and User) which to check.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership | None: Membership details.
        """
        result = await session.execute(
            select(Membership).where(
                and_(
                    Membership.company_id == parties.company_id,
                    Membership.user_id == parties.user_id,
                )
            )
        )
        membership = result.scalars().first()

        return membership

    @staticmethod
    async def send_invitation(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Send an invitation for a User to become a member of a Company.

        Args:
            parties (MembershipActionRequest):
                The requested parties (Company and User).
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: Details of the new invitation.
        """
        logger.info(
            (
                f"Received a request to invite user {parties.user_id} ",
                f"to company {parties.company_id}",
            )
        )

        invitation = Membership(
            company_id=parties.company_id,
            user_id=parties.user_id,
            status=StatusEnum.INVITED,
        )

        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)

        logger.info(
            (
                f"User {parties.user_id} successfully invited ",
                f"to company {parties.company_id}",
            )
        )
        return invitation

    @staticmethod
    async def cancel_invitation(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Cancel an invitation of a User to a Company.

        Args:
            membership (Membership): The invitation which to cancel.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to cancel invitation with ID {membership.id}")

        await session.delete(membership)
        await session.commit()

        logger.info(f"Invitation with ID {membership.id} cancelled successfully")

    @staticmethod
    async def accept_invitation(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Accept an invitation to join a Company.

        Args:
            membership (Membership): The invitation which to accept.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The accepted invitation.
        """
        logger.info(f"Received request to accept invitation with ID {membership.id}")

        setattr(membership, "status", StatusEnum.MEMBER)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Invitation with ID {membership.id} accepted successfully")

        return membership

    @staticmethod
    async def decline_invitation(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Decline an invitation to join a Company.

        Args:
            membership (Membership): The invitation which to decline.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The declined invitation.
        """
        logger.info(f"Received request to decline invitation with ID {membership.id}")

        setattr(membership, "status", StatusEnum.DECLINED)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Invitation with ID {membership.id} declined successfully")

        return membership

    @staticmethod
    async def send_request(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Send a request to join a Company.

        Args:
            parties (MembershipActionRequest):
                The requested parties (Company and User).
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: Details of the new request.
        """
        logger.info(
            (
                f"Received request from user {parties.user_id} to ask to join ",
                f"company with ID {parties.company_id}",
            )
        )

        request = Membership(
            company_id=parties.company_id,
            user_id=parties.user_id,
            status=StatusEnum.REQUESTED,
        )

        session.add(request)
        await session.commit()
        await session.refresh(request)

        logger.info(
            (
                f"Successfully sent a request from User {parties.user_id} to join ",
                f"company {parties.company_id}",
            )
        )
        return request

    @staticmethod
    async def cancel_request(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Cancel a request to join a Company.

        Args:
            membership (Membership): The request which to cancel.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to cancel request with ID {membership.id}")

        await session.delete(membership)
        await session.commit()

        logger.info(f"Request with ID {membership.id} cancelled successfully")

    @staticmethod
    async def accept_request(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Accept a request to join a Company.

        Args:
            membership (Membership): The request which to accept.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The accepted request.
        """
        logger.info(f"Received request to accept request with ID {membership.id}")

        setattr(membership, "status", StatusEnum.MEMBER)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Request with ID {membership.id} accepted successfully")

        return membership

    @staticmethod
    async def reject_request(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Reject a request to join a Company.

        Args:
            membership (Membership): The request which to reject.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The rejected request.
        """
        logger.info(f"Received request to reject request with ID {membership.id}")

        setattr(membership, "status", StatusEnum.REJECTED)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Request with ID {membership.id} rejected successfully")

        return membership

    @staticmethod
    async def terminate_membership(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Terminate a membership.

        Args:
            membership (Membership): The membership which to terminate.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to terminate membership with ID {membership.id}")

        await session.delete(membership)
        await session.commit()

        logger.info(f"Membership with ID {membership.id} terminated successfully")

    @staticmethod
    async def get_requests_by_user(
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
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a User's requests.
        """
        result = await session.execute(
            select(Membership)
            .where(
                MembershipRepo.get_common_where_clause(
                    user_id=user_id, status=StatusEnum.REQUESTED
                )
            )
            .limit(limit)
            .offset(offset)
        )
        requests = result.scalars().all()

        return requests

    @staticmethod
    async def get_invitations_by_user(
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
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a User's invitations.
        """
        result = await session.execute(
            select(Membership)
            .where(
                MembershipRepo.get_common_where_clause(
                    user_id=user_id, status=StatusEnum.INVITED
                )
            )
            .limit(limit)
            .offset(offset)
        )
        requests = result.scalars().all()

        return requests

    @staticmethod
    async def get_invitations_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        """Get invitations to join a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            limit (int, optional): How much invitations to get. Defaults to 10.
            offset (int, optional): Where to start getting invitations. Defaults to 0.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a Company's invitations.
        """
        result = await session.execute(
            select(Membership)
            .where(
                MembershipRepo.get_common_where_clause(
                    company_id=company_id, status=StatusEnum.INVITED
                )
            )
            .limit(limit)
            .offset(offset)
        )
        requests = result.scalars().all()

        return requests

    @staticmethod
    async def get_requests_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        """Get requests to join a Company.

        Args:
            company_id (UUID): ID of the Company to check.
            limit (int, optional): How much requests to get. Defaults to 10.
            offset (int, optional): Where to start getting requests. Defaults to 0.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a Company's requests.
        """
        result = await session.execute(
            select(Membership)
            .where(
                MembershipRepo.get_common_where_clause(
                    company_id=company_id, status=StatusEnum.REQUESTED
                )
            )
            .limit(limit)
            .offset(offset)
        )
        requests = result.scalars().all()

        return requests

    @staticmethod
    async def get_members_by_company(
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
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[Membership]: The list of a Company's members.
        """
        result = await session.execute(
            select(User)
            .join(Membership, User.id == Membership.user_id)
            .where(
                MembershipRepo.get_common_where_clause(
                    company_id=company_id, status=StatusEnum.MEMBER
                )
            )
            .limit(limit)
            .offset(offset)
        )
        members = result.scalars().all()

        return members

    @staticmethod
    async def appoint_admin(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Upgrade a User to an admin of a Company.

        Args:
            membership (Membership): The membership which to upgrade.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The upgraded membership.
        """
        logger.info(
            (
                f"Received request to appoint user {membership.user_id} ",
                f"an admin in company {membership.company_id}",
            )
        )

        setattr(membership, "status", StatusEnum.ADMIN)

        await session.commit()
        await session.refresh(membership)

        logger.info(
            (
                f"User {membership.user_id} successfully appointed ",
                f"an admin in company {membership.company_id}",
            )
        )

        return membership

    @staticmethod
    async def remove_admin(
        membership: Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        """Downgrade a User from being an admin of a Company.

        Args:
            membership (Membership): The membership which to downgrade.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            Membership: The downgraded membership.
        """
        logger.info(
            (
                f"Received request to remove user {membership.user_id} ",
                f"from an admin role in company {membership.company_id}",
            )
        )

        setattr(membership, "status", StatusEnum.MEMBER)

        await session.commit()
        await session.refresh(membership)

        logger.info(
            (
                f"User {membership.user_id} successfully removed ",
                f"from an admin role in company {membership.company_id}",
            )
        )

        return membership

    @staticmethod
    async def get_admins_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[User]:
        """Get a list of admins in a company.

        Args:
            company_id (UUID): The company which to check.
            limit (int, optional): How much admins to get. Defaults to 10.
            offset (int, optional): Where to start getting admins. Defaults to 0.
            session (AsyncSession):
                The database session used for querying memberships.
                Defaults to the session obtained through get_session.

        Returns:
            list[User]: The list of admins.
        """
        result = await session.execute(
            select(User)
            .join(Membership, User.id == Membership.user_id)
            .where(
                (Membership.company_id == company_id)
                & (Membership.status == StatusEnum.ADMIN)
            )
            .limit(limit)
            .offset(offset)
        )
        admins = result.scalars().all()

        return admins
