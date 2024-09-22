from typing import Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Quiz
from app.db.repo.base import BaseRepo
from app.schemas.quiz_schemas import QuizCreateRequest, QuizUpdateRequest


class QuizRepo(BaseRepo[Quiz]):
    """Represents a repository pattern to perform CRUD on Quiz model."""

    @classmethod
    def get_model(cls) -> Type[Quiz]:
        return Quiz

    @staticmethod
    async def get_quizzes_by_company(
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Quiz]:
        return await QuizRepo.get_all_by_fields(
            fields=Quiz.company_id,
            values=company_id,
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def create_quiz(
        quiz: QuizCreateRequest,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        new_quiz = Quiz(
            company_id=company_id,
            name=quiz.name,
            description=quiz.description,
            frequency=quiz.frequency,
            questions=quiz.questions.model_dump(),
        )
        return await QuizRepo.create(entity=new_quiz, session=session)

    @staticmethod
    async def update_quiz(
        existing_quiz: Quiz,
        quiz_update: QuizUpdateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        update_data = quiz_update.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        return await QuizRepo.update(
            entity=existing_quiz, update_data=update_data, session=session
        )
