from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Quiz, StatusEnum
from app.db.repo.quiz import QuizRepo
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_answer_quiz(
    fill_db_with_quizzes,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_1.email,
        company_name=payload.test_company_2.name,
        session=test_session,
    )
    quiz = await QuizRepo.get_by_fields(
        fields=[Quiz.name, Quiz.company_id],
        values=[payload.test_quiz_1.name, company_id],
        session=test_session,
    )
    assert quiz is not None, "Quiz not found"
    quiz_id = quiz.id
    time = datetime.now(ZoneInfo("Europe/Kyiv"))
    response = await client.post(
        f"/quizzes/{quiz_id}/answer", json=payload.test_quiz_1_answers.model_dump()
    )
    assert response.status_code == 200
    quiz_result = response.json()
    expected_quiz_result = {
        **payload.expected_test_quiz_1_answers,
        "user_id": user_id,
        "company_id": company_id,
        "quiz_id": str(quiz_id),
        "time": time.isoformat(),
    }
    assert_real_matches_expected(quiz_result, expected_quiz_result)
