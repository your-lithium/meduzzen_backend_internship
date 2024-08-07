from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import and_

from app.core.logger import logger
from app.db.database import get_session
from app.db.models import QuizResult


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
        """Add a new quiz result.

        Args:
            user_id (UUID): The user who answered the quiz.
            company_id (UUID): The company that the quiz belongs to.
            quiz_id (UUID): The quiz answered.
            answered (int): The amount of answered questions.
            correct (int): The amount of questions answered correctly.
            session (AsyncSession):
                The database session used for querying quiz results.
                Defaults to the session obtained through get_session.

        Returns:
            QuizResult: The new result.
        """
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
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        """Get quiz results of one User.

        Args:
            user_id (UUID): The user which to check.
            session (AsyncSession):
                The database session used for querying quiz results.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResult]: The results of a User.
        """
        result = await session.execute(
            select(QuizResult).where(QuizResult.user_id == user_id)
        )
        results = result.scalars().all()

        return results

    @staticmethod
    async def get_results_by_company(
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        """Get quiz results of Users in one Company.

        Args:
            company_id (UUID):
                The company which to check.
            session (AsyncSession):
                The database session used for querying quiz results.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResult]: The results of Users in a Company.
        """
        result = await session.execute(
            select(QuizResult).where(QuizResult.company_id == company_id)
        )
        results = result.scalars().all()

        return results

    @staticmethod
    async def get_results_by_parties(
        user_id: UUID,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResult]:
        """Get quiz results of one User in one Company.

        Args:
            user_id (UUID): The user which to check.
            company_id (UUID):
                The company which to check.
            session (AsyncSession):
                The database session used for querying quiz results.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResult]: The results of a User in the Company.
        """
        result = await session.execute(
            select(QuizResult).where(
                and_(
                    QuizResult.user_id == user_id,
                    QuizResult.company_id == company_id,
                )
            )
        )
        results = result.scalars().all()

        return results
