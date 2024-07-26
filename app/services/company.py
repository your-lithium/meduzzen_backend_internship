from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Company, User
from app.db.repo.company import CompanyRepo
from app.schemas.company_schemas import (CompanyCreateRequest,
                                         CompanyUpdateRequest)
from app.services.exceptions import (CompanyNameAlreadyExistsError,
                                     CompanyNotFoundError)
from app.services.permissions import PermissionService


def get_company_service():
    return CompanyService()


class CompanyService:
    """Represents a service for handling requests to Company model."""

    async def get_all_companies(
        self,
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
        companies: list[Company] = await CompanyRepo.get_all_companies(
            limit=limit,
            offset=offset,
            session=session,
        )
        return companies

    async def get_company_by_id(
        self,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Get details for one company.

        Args:
            company_id (UUID): The company's ID.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Raises:
            CompanyNotFoundError: If the requested company does not exist.

        Returns:
            Company: Company details.
        """
        company: Company | None = await CompanyRepo.get_company_by_id(
            company_id=company_id, session=session
        )

        if company is None:
            raise CompanyNotFoundError(company_id)

        return company

    async def create_company(
        self,
        company: CompanyCreateRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Creates a new company from details provided.

        Args:
            company (CompanyCreateRequest): Details for the new company.
            current_user (User): The current authenticated user.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Returns:
            Company: The created company.
        """
        check_name: Company | None = await CompanyRepo.get_company_by_name(
            company_name=company.name, session=session
        )
        if check_name is not None:
            raise CompanyNameAlreadyExistsError(object_value=company.name)

        company: Company | None = await CompanyRepo.create_company(
            company=company, owner=current_user, session=session
        )

        return company

    async def update_company(
        self,
        company_id: UUID,
        company_update: CompanyUpdateRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Update an existing company.

        Args:
            company_id (UUID): The company's ID.
            company_update (CompanyUpdateRequest):
                The details which to update in a company.
            current_user (User): The current authenticated user.
            session (AsyncSession):
                The database session used for querying companies.
                Defaults to the session obtained through get_session.

        Raises:
            CompanyNotFoundError: If the requested company does not exist.
            AccessDeniedError:
                If the current authenticated user is not the company's owner.
            NameAlreadyExistsError: If the name provided has already been used.

        Returns:
            Company: Details of the updated company.
        """
        existing_company = await self.get_company_by_id(
            company_id=company_id, session=session
        )

        PermissionService.grant_owner_permission(
            owner_id=existing_company.owner_id,
            current_user_id=current_user.id,
            operation="update",
        )

        if company_update.name:
            check_name: Company | None = await CompanyRepo.get_company_by_name(
                company_name=company_update.name, session=session
            )
            if check_name is not None:
                raise CompanyNameAlreadyExistsError(object_value=company_update.name)

        updated_company: Company = await CompanyRepo.update_company(
            existing_company=existing_company,
            company_update=company_update,
            session=session,
        )

        return updated_company

    async def delete_company(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Delete a company.

        Args:
            company_id (UUID): The company's ID.
            current_user (User): The current authenticated user.
            session (AsyncSession):
                The database session used for querying company.
                Defaults to the session obtained through get_session.

        Raises:
            CompanyNotFoundError: If the requested company does not exist.
            AccessDeniedError:
                If the current authenticated user is not the company's owner.
        """
        company: Company | None = await self.get_company_by_id(
            company_id=company_id, session=session
        )

        PermissionService.grant_owner_permission(
            owner_id=company.owner_id,
            current_user_id=current_user.id,
            operation="delete",
        )

        await CompanyRepo.delete_company(company=company, session=session)
