from typing import Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import QuizResult
from app.db.repo.base import BaseRepo


class QuizResultRepo(BaseRepo[QuizResult]):
    """Represents a repository pattern to perform CRUD on QuizResult model."""

    @classmethod
    def get_model(cls) -> Type[QuizResult]:
        return QuizResult

    @staticmethod
    async def add_result(
        user_id: UUID,
        company_id: UUID,
        quiz_id: UUID,
        answered: int,
        correct: int,
        session: AsyncSession = Depends(get_session),
    ) -> QuizResult:
        new_result = QuizResult(
            user_id=user_id,
            company_id=company_id,
            quiz_id=quiz_id,
            answered=answered,
            correct=correct,
        )
        return await QuizResultRepo.create(entity=new_result, session=session)

    @staticmethod
    async def get_results_by_user(
        user_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        return await QuizResultRepo.get_all_by_fields(
            fields=[QuizResult.user_id],
            values=[user_id],
            limit=None,
            offset=0,
            session=session,
        )

    @staticmethod
    async def get_results_by_company(
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        return await QuizResultRepo.get_all_by_fields(
            fields=[QuizResult.company_id],
            values=[company_id],
            limit=None,
            offset=0,
            session=session,
        )

    @staticmethod
    async def get_results_by_parties(
        user_id: UUID,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        return await QuizResultRepo.get_all_by_fields(
            fields=[QuizResult.user_id, QuizResult.company_id],
            values=[user_id, company_id],
            limit=None,
            offset=0,
            session=session,
        )
