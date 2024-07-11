from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.database import get_session
from app.db.models import Company, User
from app.schemas.company_schemas import CompanyCreateRequest, CompanyUpdateRequest
from app.core.logger import logger


class CompanyRepo:
    """Represents a repository pattern to perform CRUD on User model."""

    @staticmethod
    async def get_all_companies(
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Company]:
        """Get a list of companies.

        Args:
            limit (int, optional): How much companies to get. Defaults to 10.
            offset (int, optional): Where to start getting companies. Defaults to 0.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            list[Company]: The list of companies.
        """
        result = await session.execute(
            select(Company).where(Company.is_public).limit(limit).offset(offset)
        )
        companies = result.scalars().all()

        return companies

    @staticmethod
    async def get_company_by_id(
        company_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> Company | None:
        """Get details for one company via its ID.

        Args:
            company_id (UUID): The company's ID.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            Company | None: Company details.
        """
        result = await session.execute(select(Company).where(Company.id == company_id))
        company = result.scalars().first()

        return company

    @staticmethod
    async def get_company_by_name(
        company_name: str, session: AsyncSession = Depends(get_session)
    ) -> Company | None:
        """Get details for one company via its name.

        Args:
            company_name (str): The name which to check.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            Company | None: Company details.
        """
        result = await session.execute(
            select(Company).where(Company.name == company_name)
        )
        company = result.scalars().first()

        return company

    @staticmethod
    async def create_company(
        company: CompanyCreateRequest,
        owner: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Create a new company.

        Args:
            company (SignUpRequest): Details for creating a new company.
            owner (User): The current owner.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            Company: Details of the new company.
        """
        logger.info("Received a company creation request")

        new_company = Company(
            name=company.name,
            description=company.description,
            owner_id=owner.id,
            is_public=company.is_public,
        )

        session.add(new_company)
        await session.commit()
        await session.refresh(new_company)

        logger.info("New company created successfully")
        return new_company

    @staticmethod
    async def update_company(
        existing_company: Company,
        company_update: CompanyUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Update an existing company.

        Args:
            existing_company (Company): The existing company to update
            company_update (CompanyUpdateRequest):
                The details which to update in a company.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            Company: Details of the updated company.
        """
        logger.info(f"Received request to update company with ID {existing_company.id}")

        for attr in company_update.__dict__:
            value = getattr(company_update, attr)
            if value is not None:
                setattr(existing_company, attr, value)

        await session.commit()
        await session.refresh(existing_company)

        logger.info(f"Company with ID {existing_company.id} updated successfully")
        return existing_company

    @staticmethod
    async def delete_company(
        company: Company, session: AsyncSession = Depends(get_session)
    ) -> None:
        """Delete a company.

        Args:
            company (Company): The existing company to delete.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to delete company with ID {company.id}")

        await session.delete(company)
        await session.commit()

        logger.info(f"Company with ID {company.id} deleted successfully")
