from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.sql import and_

from app.db.database import get_session
from app.db.models import QuizResult
from app.core.logger import logger


class QuizResultRepo:
    """Represents a repository pattern to perform CRUD on QuizResult model."""

    @staticmethod
    async def add_result(
        user_id: UUID,
        company_id: UUID,
        quiz_id: UUID,
        answered: int,
        correct: int,
        session: AsyncSession = Depends(get_session),
    ) -> QuizResult:
        logger.info("Received a request to add a new quiz result")

        new_result = QuizResult(
            user_id=user_id,
            company_id=company_id,
            quiz_id=quiz_id,
            answered=answered,
            correct=correct,
        )

        session.add(new_result)
        await session.commit()

        logger.info("New quiz result added successfully")
        return new_result

    @staticmethod
    async def get_results_by_user(
        user_id: UUID,
        company_id: UUID | None = None,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        if company_id:
            result = await session.execute(
                select(QuizResult).where(
                    and_(
                        QuizResult.user_id == user_id,
                        QuizResult.company_id == company_id,
                    )
                )
            )
        else:
            result = await session.execute(
                select(QuizResult).where(QuizResult.user_id == user_id)
            )
        results = result.scalars().all()

        return results
