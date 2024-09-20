import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Quiz
from app.db.repo.quiz import QuizRepo
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
async def test_create_quiz(
    fill_db_with_quizzes, client: AsyncClient, test_session: AsyncSession
):
    _, company_id = await get_user_and_company_ids(
        company_name=payload.test_company_1.name, session=test_session
    )
    response = await client.post(
        f"/quizzes/{company_id}", json=payload.test_quiz_3.model_dump()
    )
    assert response.status_code == 200
    quiz = response.json()
    expected_quiz = {
        **payload.expected_test_quiz_3,
        "company_id": company_id,
    }
    assert_real_matches_expected(quiz, expected_quiz)


@pytest.mark.asyncio
async def test_get_quizzes_by_company(
    fill_db_with_quizzes, client: AsyncClient, test_session: AsyncSession
):
    _, company_id = await get_user_and_company_ids(
        company_name=payload.test_company_1.name, session=test_session
    )
    response = await client.get(f"/quizzes/{company_id}")
    assert response.status_code == 200

    quizzes = response.json()
    expected_quizzes = [
        payload.expected_test_quiz_1,
        payload.expected_test_quiz_2,
        payload.expected_test_quiz_2,
    ]
    company_names = [
        payload.test_company_1.name,
        payload.test_company_1.name,
        payload.test_company_2.name,
    ]
    for quiz, expected_quiz, company_name in zip(
        quizzes, expected_quizzes, company_names
    ):
        expected_quiz = {
            **expected_quiz,
            "company_id": (
                await get_user_and_company_ids(
                    company_name=company_name, session=test_session
                )
            )[1],
        }
        assert_real_matches_expected(quiz, expected_quiz)


@pytest.mark.asyncio
async def test_update_quiz(
    fill_db_with_quizzes, client: AsyncClient, test_session: AsyncSession
):
    _, company_id = await get_user_and_company_ids(
        company_name=payload.test_company_1.name, session=test_session
    )
    quiz = await QuizRepo.get_by_fields(
        fields=[Quiz.name, Quiz.company_id],
        values=[payload.test_quiz_1.name, company_id],
        session=test_session,
    )
    assert quiz is not None, "Quiz not found"
    quiz_id = quiz.id
    response = await client.patch(
        f"/quizzes/{quiz_id}", json=payload.test_quiz_1_update.model_dump()
    )
    assert response.status_code == 200
    updated_quiz = response.json()
    expected_quiz = {
        **payload.expected_test_quiz_1_update,
        "company_id": company_id,
    }
    assert_real_matches_expected(updated_quiz, expected_quiz)


@pytest.mark.asyncio
async def test_delete_quiz(
    fill_db_with_quizzes, client: AsyncClient, test_session: AsyncSession
):
    quiz = await QuizRepo.get_by_fields(
        fields=Quiz.name, values=payload.test_quiz_1.name, session=test_session
    )
    assert quiz is not None, "Quiz not found"
    quiz_id = quiz.id
    await client.delete(f"/quizzes/{quiz_id}")
    quiz = await QuizRepo.get_by_id(record_id=quiz_id, session=test_session)
    assert quiz is None
