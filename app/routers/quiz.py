from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse

from app.db.database import get_session
from app.db.models import User
from app.schemas.quiz_result_schemas import (Answers, MeanScore,
                                             QuizResultDetails)
from app.schemas.quiz_schemas import (QuizCreateRequest, QuizResponse,
                                      QuizUpdateRequest)
from app.services.auth import get_current_user
from app.services.quiz import QuizService, get_quiz_service
from app.services.quiz_result import QuizResultService, get_quiz_result_service

router = APIRouter(prefix="/quizzes", tags=["Quiz Methods"])


@router.get("/{company_id}", response_model=list[QuizResponse])
async def get_quizzes_by_company(
    company_id: UUID,
    limit: int = 10,
    offset: int = 0,
    quiz_service: QuizService = Depends(get_quiz_service),
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
    quiz_service: QuizService = Depends(get_quiz_service),
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
    quiz_service: QuizService = Depends(get_quiz_service),
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
    quiz_service: QuizService = Depends(get_quiz_service),
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
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
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
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_rating(
        user_id=user_id, company_id=company_id, session=session
    )

    return rating


@router.get("/{user_id}/result", response_model=MeanScore)
async def get_user_rating(
    user_id: UUID,
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
):
    rating = await quiz_result_service.get_user_rating(user_id=user_id, session=session)

    return rating


@router.get("/results/me")
async def get_user_results_48h(
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    get_csv: bool = False,
):
    results = await quiz_result_service.get_user_results_48h(
        current_user=current_user, get_csv=get_csv
    )
    if get_csv:
        results = FileResponse(results)
    return results


@router.get("/results/company/{company_id}")
async def get_company_results_48h(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
    get_csv: bool = False,
):
    results = await quiz_result_service.get_company_results_48h(
        company_id=company_id,
        current_user=current_user,
        session=session,
        get_csv=get_csv,
    )
    if get_csv:
        results = FileResponse(results)
    return results


@router.get("/results/company/{company_id}/{user_id}")
async def get_company_user_results_48h(
    company_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
    get_csv: bool = False,
):
    results = await quiz_result_service.get_company_user_results_48h(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
        get_csv=get_csv,
    )
    if get_csv:
        results = FileResponse(results)
    return results


@router.get("/results/quiz/{quiz_id}")
async def get_quiz_results_48h(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_result_service: QuizResultService = Depends(get_quiz_result_service),
    session: AsyncSession = Depends(get_session),
    get_csv: bool = False,
):
    results = await quiz_result_service.get_quiz_results_48h(
        quiz_id=quiz_id, current_user=current_user, session=session, get_csv=get_csv
    )
    if get_csv:
        results = FileResponse(results)
    return results
