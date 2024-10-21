from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QuizResult, StatusEnum
from app.db.repo.quiz_result import QuizResultRepo
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_user_company_rating(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/analytics/{user_id}/rating/{company_id}")
    assert response.status_code == 200
    rating = response.json()
    assert rating == payload.expected_test_user_2_rating


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_user_rating(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, _ = await get_user_and_company_ids(
        user_email=payload.test_user_1.email, session=test_session
    )
    response = await client.get(f"/analytics/{user_id}/rating")
    assert response.status_code == 200
    rating = response.json()
    assert rating == payload.expected_test_user_1_rating


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_current_user_dynamics(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    time = datetime.now(ZoneInfo("Europe/Kyiv"))
    response = await client.get("/analytics/me/dynamics")
    assert response.status_code == 200
    mean_scores_timed = response.json()
    for mean_score_timed, expected_mean_score in zip(
        mean_scores_timed, payload.expected_test_user_1_dynamics_scores
    ):
        expected_mean_score_timed = {
            "time": time.isoformat(),
            "mean_score": expected_mean_score,
        }
        assert_real_matches_expected(
            real=mean_score_timed, expected=expected_mean_score_timed
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_current_user_latest_answers(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, _ = await get_user_and_company_ids(
        user_email=payload.test_user_1.email, session=test_session
    )
    all_answers = await QuizResultRepo.get_all_by_fields(
        fields=[QuizResult.user_id], values=[user_id], session=test_session
    )

    response = await client.get("/analytics/me/latest_answers")
    assert response.status_code == 200
    latest_answers = response.json()

    latest_answers_by_quiz: dict[UUID, QuizResult] = {}
    for answer in all_answers:
        current_latest = latest_answers_by_quiz.get(answer.quiz_id)
        if current_latest is None or answer.time > current_latest.time:
            latest_answers_by_quiz[answer.quiz_id] = answer

    expected_latest_answers = [
        {
            "quiz_id": str(quiz_id),
            "time": answer.time.replace(tzinfo=ZoneInfo("Europe/Kyiv")).isoformat(),
        }
        for quiz_id, answer in latest_answers_by_quiz.items()
    ]

    for latest_answer, expected_answer in zip(latest_answers, expected_latest_answers):
        assert_real_matches_expected(real=latest_answer, expected=expected_answer)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_company_dynamics(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    time = datetime.now(ZoneInfo("Europe/Kyiv"))
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/analytics/{company_id}/dynamics")
    assert response.status_code == 200
    user_mean_scores_timed = response.json()

    for user_mean_score_timed in user_mean_scores_timed:
        expected_scores = [
            {"time": time.isoformat(), "mean_score": score}
            for score in payload.expected_test_user_2_dynamics_scores
        ]
        assert user_mean_score_timed["user_id"] == user_id
        for real_score, expected_score in zip(
            user_mean_score_timed["scores"], expected_scores
        ):
            assert_real_matches_expected(real=real_score, expected=expected_score)


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_company_member_dynamics(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    time = datetime.now(ZoneInfo("Europe/Kyiv"))
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    response = await client.get(f"/analytics/{company_id}/dynamics/{user_id}")
    assert response.status_code == 200
    mean_scores_timed = response.json()
    for mean_score_timed, expected_mean_score in zip(
        mean_scores_timed, payload.expected_test_user_2_dynamics_scores
    ):
        expected_mean_score_timed = {
            "time": time.isoformat(),
            "mean_score": expected_mean_score,
        }
        assert_real_matches_expected(
            real=mean_score_timed, expected=expected_mean_score_timed
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("fill_db_with_memberships", [StatusEnum.MEMBER], indirect=True)
async def test_get_company_latest_answers(
    fill_db_with_quiz_results,
    fill_db_with_memberships,
    client: AsyncClient,
    test_session: AsyncSession,
):
    user_id, company_id = await get_user_and_company_ids(
        user_email=payload.test_user_2.email,
        company_name=payload.test_company_1.name,
        session=test_session,
    )
    all_answers = await QuizResultRepo.get_all_by_fields(
        fields=[QuizResult.user_id], values=[user_id], session=test_session
    )

    response = await client.get(f"/analytics/{company_id}/latest_answers")
    assert response.status_code == 200
    user_latest_answers = response.json()

    latest_answers_by_quiz: dict[UUID, QuizResult] = {}
    for answer in all_answers:
        current_latest = latest_answers_by_quiz.get(answer.quiz_id)
        if current_latest is None or answer.time > current_latest.time:
            latest_answers_by_quiz[answer.quiz_id] = answer

    expected_latest_answers = [
        {
            "quiz_id": str(quiz_id),
            "time": answer.time.replace(tzinfo=ZoneInfo("Europe/Kyiv")).isoformat(),
        }
        for quiz_id, answer in latest_answers_by_quiz.items()
    ]

    for user_latest_answer in user_latest_answers:
        assert user_latest_answer["user_id"] == user_id
        for real_latest_answer, expected_latest_answer in zip(
            user_latest_answer["latest_answers"], expected_latest_answers
        ):
            assert_real_matches_expected(
                real=real_latest_answer, expected=expected_latest_answer
            )
