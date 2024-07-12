from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.database import get_session
from app.db.models import Quiz
from app.schemas.quiz_schemas import QuizCreateRequest, QuizUpdateRequest
from app.core.logger import logger


class QuizRepo:
    """Represents a repository pattern to perform CRUD on Quiz model."""

    @staticmethod
    async def get_quizzes_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Quiz]:
        """Get a list of quizzes belonging to one Company.

        Args:
            company_id (UUID): The ID of the company to check.
            limit (int, optional): How much quizzes to get. Defaults to 10.
            offset (int, optional): Where to start getting quizzes. Defaults to 0.
            session (AsyncSession):
                The database session used for querying quizzes.
                Defaults to the session obtained through get_session.

        Returns:
            list[Quiz]: The list of quizzes.
        """
        result = await session.execute(
            select(Quiz)
            .where(Quiz.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        quizzes = result.scalars().all()

        return quizzes

    @staticmethod
    async def get_quiz_by_id(
        quiz_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> Quiz | None:
        """Get details for one quiz via its ID.

        Args:
            quiz_id (UUID): The quiz's ID.
            session (AsyncSession):
                The database session used for querying quizzes.
                Defaults to the session obtained through get_session.

        Returns:
            Quiz | None: Quiz details.
        """
        result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
        quiz = result.scalars().first()

        return quiz

    @staticmethod
    async def create_quiz(
        quiz: QuizCreateRequest,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        """Create a new quiz.

        Args:
            quiz (QuizCreateRequest): Details for creating a new quiz.
            company_id (UUID): The company which the quiz should belong to.
            session (AsyncSession):
                The database session used for querying quizzes.
                Defaults to the session obtained through get_session.

        Returns:
            Quiz: Details of the new quiz.
        """
        logger.info("Received a quiz creation request")

        new_quiz = Quiz(
            company_id=company_id,
            name=quiz.name,
            description=quiz.description,
            frequency=quiz.frequency,
            questions=quiz.questions.model_dump(),
        )

        session.add(new_quiz)
        await session.commit()
        await session.refresh(new_quiz)

        logger.info("New quiz created successfully")
        return new_quiz

    @staticmethod
    async def update_quiz(
        existing_quiz: Quiz,
        quiz_update: QuizUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        """Update an existing quiz.

        Args:
            existing_quiz (Quiz): The existing quiz to update.
            quiz_update (QuizUpdateRequest): The details which to update in a quiz.
            session (AsyncSession):
                The database session used for querying quizzes.
                Defaults to the session obtained through get_session.

        Returns:
            Quiz: Details of the updated quiz.
        """
        logger.info(f"Received request to update quiz with ID {existing_quiz.id}")

        for attr in quiz_update.__dict__:
            value = getattr(quiz_update, attr)
            if value is not None:
                setattr(existing_quiz, attr, value)

        await session.commit()
        await session.refresh(existing_quiz)

        logger.info(f"Quiz with ID {existing_quiz.id} updated successfully")
        return existing_quiz

    @staticmethod
    async def delete_quiz(
        quiz: Quiz, session: AsyncSession = Depends(get_session)
    ) -> None:
        """Delete a quiz.

        Args:
            quiz (Quiz): The existing quiz which to delete.
            session (AsyncSession):
                The database session used for querying quizzes.
                Defaults to the session obtained through get_session.
        """
        logger.info(f"Received request to delete quiz with ID {quiz.id}")

        await session.delete(quiz)
        await session.commit()

        logger.info(f"Quiz with ID {quiz.id} deleted successfully")
