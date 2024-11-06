from typing import Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Company, User
from app.db.repo.base import BaseRepo
from app.schemas.company_schemas import CompanyCreateRequest, CompanyUpdateRequest


class CompanyRepo(BaseRepo[Company]):
    """Represents a repository pattern to perform CRUD on Company model."""

    @classmethod
    def get_model(cls) -> Type[Company]:
        return Company

    @staticmethod
    async def get_all_visible_companies(
        current_user: User,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Company]:
        return await CompanyRepo.get_all_by_fields(
            fields=[Company.is_public, Company.owner_id],
            values=[True, current_user.id],
            limit=limit,
            offset=offset,
            or_flag=True,
            session=session,
        )

    @staticmethod
    async def get_company_by_name(
        company_name: str, session: AsyncSession = Depends(get_session)
    ) -> Company | None:
        return await CompanyRepo.get_by_fields(
            fields=[Company.name], values=[company_name], session=session
        )

    @staticmethod
    async def create_company(
        company: CompanyCreateRequest,
        owner: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        new_company = Company(
            name=company.name,
            description=company.description,
            owner_id=owner.id,
            is_public=company.is_public,
        )
        return await CompanyRepo.create(entity=new_company, session=session)

    @staticmethod
    async def update_company(
        existing_company: Company,
        company_update: CompanyUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        update_data = company_update.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        return await CompanyRepo.update(
            entity=existing_company, update_data=update_data, session=session
        )
