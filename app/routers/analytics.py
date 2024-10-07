from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import User
from app.schemas.quiz_result_schemas import (
    LatestQuizAnswer,
    MeanScore,
    MeanScoreTimed,
    UserLatestQuizAnswers,
    UserMeanScoreTimed,
)
from app.services.auth import get_current_user
from app.services.quiz_result import QuizResultService, get_quiz_result_service

router = APIRouter(prefix="/analytics", tags=["Analytics Methods"])


@router.get("/{user_id}/rating/{company_id}", response_model=MeanScore)
async def get_user_company_rating(
    user_id: UUID,
    company_id: UUID,
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_company_rating(
        user_id=user_id, company_id=company_id, session=session
    )
    return rating


@router.get("/{user_id}/rating", response_model=MeanScore)
async def get_user_rating(
    user_id: UUID,
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_rating(user_id=user_id, session=session)
    return rating


@router.get("/me/dynamics", response_model=list[MeanScoreTimed])
async def get_current_user_dynamics(
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    mean_scores_timed = await quiz_result_service.get_user_dynamics(
        current_user=current_user, session=session
    )
    return mean_scores_timed


@router.get("/me/latest_answers", response_model=list[LatestQuizAnswer])
async def get_current_user_latest_answers(
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    latest_answers = await quiz_result_service.get_current_user_latest_answers(
        current_user=current_user, session=session
    )
    return latest_answers


@router.get("/{company_id}/dynamics", response_model=list[UserMeanScoreTimed])
async def get_company_dynamics(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    user_mean_scores_timed = await quiz_result_service.get_company_dynamics(
        company_id=company_id, current_user=current_user, session=session
    )
    return user_mean_scores_timed


@router.get("/{company_id}/dynamics/{user_id}", response_model=list[MeanScoreTimed])
async def get_company_member_dynamics(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    mean_scores_timed = await quiz_result_service.get_company_member_dynamics(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )
    return mean_scores_timed


@router.get("/{company_id}/latest_answers", response_model=list[UserLatestQuizAnswers])
async def get_company_latest_answers(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    user_latest_answers = await quiz_result_service.get_company_latest_answers(
        company_id=company_id, current_user=current_user, session=session
    )
    return user_latest_answers
