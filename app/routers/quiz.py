from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.quiz_schemas import (
    QuizResponse,
    QuizCreateRequest,
    QuizUpdateRequest,
)
from app.schemas.quiz_result_schemas import QuizResultDetails, Answers, MeanScore
from app.services.quiz import get_quiz_service
from app.services.quiz_result import get_quiz_result_service
from app.db.database import get_session
from app.db.models import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/quizzes")


@router.get("/{company_id}", response_model=list[QuizResponse])
async def get_quizzes_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    quiz_service=Depends(get_quiz_service),
    session: AsyncSession = Depends(get_session),
):
    quizzes = await quiz_service.get_quizzes_by_company(
        company_id=company_id, limit=limit, offset=offset, session=session
    )

    return quizzes


@router.post("/{company_id}", response_model=QuizResponse)
async def create_quiz(
    quiz: QuizCreateRequest,
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_service=Depends(get_quiz_service),
    session: AsyncSession = Depends(get_session),
):
    quiz = await quiz_service.create_quiz(
        quiz=quiz, company_id=company_id, current_user=current_user, session=session
    )

    return quiz


@router.patch("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: UUID,
    quiz_update: QuizUpdateRequest,
    current_user: User = Depends(get_current_user),
    quiz_service=Depends(get_quiz_service),
    session: AsyncSession = Depends(get_session),
):
    quiz = await quiz_service.update_quiz(
        quiz_id=quiz_id,
        quiz_update=quiz_update,
        current_user=current_user,
        session=session,
    )

    return quiz


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_service=Depends(get_quiz_service),
    session: AsyncSession = Depends(get_session),
):
    await quiz_service.delete_quiz(
        quiz_id=quiz_id, current_user=current_user, session=session
    )


@router.post("/{quiz_id}/answer", response_model=QuizResultDetails)
async def answer_quiz(
    quiz_id: UUID,
    answers: Answers,
    current_user: User = Depends(get_current_user),
    quiz_result_service=Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    result = await quiz_result_service.add_result(
        quiz_id=quiz_id, answers=answers, current_user=current_user, session=session
    )

    return result


@router.get("/{user_id}/result/{company_id}", response_model=MeanScore)
async def get_user_company_rating(
    user_id: UUID,
    company_id: UUID,
    quiz_result_service=Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_rating(
        user_id=user_id, company_id=company_id, session=session
    )

    return rating


@router.get("/{user_id}/result", response_model=MeanScore)
async def get_user_rating(
    user_id: UUID,
    quiz_result_service=Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_rating(user_id=user_id, session=session)

    return rating
