from typing import Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Membership, StatusEnum
from app.db.repo.base import BaseRepo
from app.schemas.membership_schemas import (
    MembershipActionRequest,
    MembershipUpdateRequest,
)


class MembershipRepo(BaseRepo[Membership]):
    """Represents a repository pattern to perform CRUD on Membership model."""

    @classmethod
    def get_model(cls) -> Type[Membership]:
        return Membership

    @staticmethod
    async def get_membership_by_parties(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership | None:
        return await MembershipRepo.get_by_fields(
            fields=[Membership.company_id, Membership.user_id],
            values=[parties.company_id, parties.user_id],
            session=session,
        )

    @staticmethod
    async def send_invitation(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        invitation = Membership(
            company_id=parties.company_id,
            user_id=parties.user_id,
            status=StatusEnum.INVITED,
        )
        return await MembershipRepo.create(entity=invitation, session=session)

    @staticmethod
    async def send_request(
        parties: MembershipActionRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        request = Membership(
            company_id=parties.company_id,
            user_id=parties.user_id,
            status=StatusEnum.REQUESTED,
        )
        return await MembershipRepo.create(entity=request, session=session)

    @staticmethod
    async def get_requests_by_user(
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.user_id, Membership.status],
            values=[user_id, StatusEnum.REQUESTED],
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def get_invitations_by_user(
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.user_id, Membership.status],
            values=[user_id, StatusEnum.INVITED],
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def get_invitations_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.company_id, Membership.status],
            values=[company_id, StatusEnum.INVITED],
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def get_requests_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.company_id, Membership.status],
            values=[company_id, StatusEnum.REQUESTED],
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def get_memberships_by_company(
        company_id: UUID,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.company_id, Membership.status],
            values=[company_id, StatusEnum.MEMBER],
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def update_status(
        membership: Membership,
        status: StatusEnum,
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        membership_update = MembershipUpdateRequest(status=status)
        update_data = membership_update.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        return await MembershipRepo.update(
            entity=membership, update_data=update_data, session=session
        )

    @staticmethod
    async def get_admin_memberships_by_company(
        company_id: UUID,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Membership]:
        return await MembershipRepo.get_all_by_fields(
            fields=[Membership.company_id, Membership.status],
            values=[company_id, StatusEnum.ADMIN],
            limit=limit,
            offset=offset,
            session=session,
        )
