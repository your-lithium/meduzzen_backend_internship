from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import User
from app.schemas.company_schemas import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyUpdateRequest,
)
from app.services.auth import get_current_user
from app.services.company import CompanyService, get_company_service

router = APIRouter(prefix="/companies", tags=["Company Methods"])


@router.get("", response_model=list[CompanyResponse])
async def read_all_companies(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_session),
):
    companies = await company_service.get_all_visible_companies(
        limit=limit, offset=offset, current_user=current_user, session=session
    )

    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def read_company_by_id(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_session),
):
    company = await company_service.get_company_by_id(
        company_id=company_id, current_user=current_user, session=session
    )

    return company


@router.post("", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreateRequest,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_session),
):
    company = await company_service.create_company(
        company=company, current_user=current_user, session=session
    )

    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_update: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_session),
):
    company = await company_service.update_company(
        company_id=company_id,
        company_update=company_update,
        current_user=current_user,
        session=session,
    )

    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_session),
):
    await company_service.delete_company(
        company_id=company_id, current_user=current_user, session=session
    )
