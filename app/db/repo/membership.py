from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.sql import and_

from app.db.database import get_session
from app.db.models import Membership, StatusEnum, User
from app.schemas.membership_schemas import MembershipActionRequest
from app.core.logger import logger


class MembershipRepo:
    """Represents a repository pattern to perform CRUD on Membership model."""

    @staticmethod
    async def get_membership_by_id(
        membership_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        result = await session.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalars().first()

        return membership

    @staticmethod
    async def get_membership_by_parties(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
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

        logger.info(
            (
                f"User {parties.user_id} successfully invited ",
                f"to company {parties.company_id}",
            )
        )
        return invitation

    @staticmethod
    async def cancel_invitation(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        logger.info(f"Received request to cancel invitation with ID {membership.id}")

        await session.delete(membership)
        await session.commit()

        logger.info(f"Invitation with ID {membership.id} cancelled successfully")

    @staticmethod
    async def accept_invitation(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        logger.info(f"Received request to accept invitation with ID {membership.id}")

        setattr(membership, "status", StatusEnum.MEMBER)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Invitation with ID {membership.id} accepted successfully")

        return membership

    @staticmethod
    async def decline_invitation(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        logger.info(f"Received request to decline invitation with ID {membership.id}")

        setattr(membership, "status", StatusEnum.DECLINED)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Invitation with ID {membership.id} declined successfully")

        return membership

    @staticmethod
    async def send_request(
        parties=MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
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

        logger.info(
            (
                f"Successfully sent a request from User {parties.user_id} to join ",
                f"company {parties.company_id}",
            )
        )
        return request

    @staticmethod
    async def cancel_request(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        logger.info(f"Received request to cancel request with ID {membership.id}")

        await session.delete(membership)
        await session.commit()

        logger.info(f"Request with ID {membership.id} cancelled successfully")

    @staticmethod
    async def accept_request(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        logger.info(f"Received request to accept request with ID {membership.id}")

        setattr(membership, "status", StatusEnum.MEMBER)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Request with ID {membership.id} accepted successfully")

        return membership

    @staticmethod
    async def reject_request(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        logger.info(f"Received request to reject request with ID {membership.id}")

        setattr(membership, "status", StatusEnum.REJECTED)

        await session.commit()
        await session.refresh(membership)

        logger.info(f"Request with ID {membership.id} rejected successfully")

        return membership

    @staticmethod
    async def terminate_membership(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> None:
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
        result = await session.execute(
            select(Membership)
            .where(
                and_(
                    Membership.user_id == user_id,
                    Membership.status == StatusEnum.REQUESTED,
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
        result = await session.execute(
            select(Membership)
            .where(
                and_(
                    Membership.user_id == user_id,
                    Membership.status == StatusEnum.INVITED,
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
        result = await session.execute(
            select(Membership)
            .where(
                and_(
                    Membership.company_id == company_id,
                    Membership.status == StatusEnum.INVITED,
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
        result = await session.execute(
            select(Membership)
            .where(
                and_(
                    Membership.company_id == company_id,
                    Membership.status == StatusEnum.REQUESTED,
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
        result = await session.execute(
            select(User)
            .join(Membership, User.id == Membership.user_id)
            .where(
                and_(
                    Membership.company_id == company_id,
                    Membership.status == StatusEnum.MEMBER,
                )
            )
            .limit(limit)
            .offset(offset)
        )
        members = result.scalars().all()

        return members

    @staticmethod
    async def appoint_admin(
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
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
        membership=Membership,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
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
