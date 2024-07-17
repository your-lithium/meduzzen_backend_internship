from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from datetime import timedelta

from app.db.models import User, Quiz, QuizResult, StatusEnum
from app.schemas.quiz_result_schemas import Answers, QuizResultDetails
from app.schemas.membership_schemas import MembershipActionRequest
from app.db.repo.quiz_result import QuizResultRepo
from app.services.exceptions import (
    ResultsNotFoundError,
    AccessDeniedError,
    IncompleteQuizError,
)
from app.db.database import get_session
from app.services.company import get_company_service, CompanyService
from app.services.user import get_user_service, UserService
from app.services.membership import get_membership_service, MembershipService
from app.services.quiz import get_quiz_service, QuizService
from app.services.redis_connect import redis_client


def get_quiz_result_service(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    membership_service=Depends(get_membership_service),
    quiz_service=Depends(get_quiz_service),
):
    return QuizResultService(
        user_service, company_service, membership_service, quiz_service
    )


class QuizResultService:
    """Represents a service for handling requests to QuizResult model."""

    def __init__(
        self,
        user_service: UserService,
        company_service: CompanyService,
        membership_service: MembershipService,
        quiz_service: QuizService,
    ) -> None:
        self._user_service = user_service
        self._company_service = company_service
        self._membership_service = membership_service
        self._quiz_service = quiz_service

    async def check_company_member_and_quiz(
        self,
        quiz_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        """Check if the Quiz exists and a User is a member of its Company.

        Args:
            quiz_id (UUID): The ID of the Quiz requested.
            current_user (User): The User who to authorize.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            AccessDeniedError:
                If the User isn't a member of the Company that owns the Quiz.

        Returns:
            Quiz: Quiz details.
        """
        quiz = await self._quiz_service.get_quiz_by_id(quiz_id=quiz_id, session=session)

        parties = MembershipActionRequest(
            company_id=quiz.company_id, user_id=current_user.id
        )
        existing_membership = await self._membership_service.get_membership_by_parties(
            parties=parties, session=session
        )

        if existing_membership.status != StatusEnum.MEMBER:
            raise AccessDeniedError(
                "You're not allowed to take quizzes of companies you're not a member of"
            )

        return quiz

    async def store_quiz_result(self, quiz_result: QuizResultDetails):
        await redis_client.connect()
        key = (
            f"quiz_result:{quiz_result.user_id}:{quiz_result.company_id}:"
            f"{quiz_result.quiz_id}:{quiz_result.time}"
        )
        value = quiz_result.model_dump_json()
        ttl = int(timedelta(hours=48).total_seconds())
        await redis_client.setex(key, value, ttl)
        await redis_client.close()

    async def add_result(
        self,
        quiz_id: UUID,
        answers: Answers,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> QuizResult:
        """Add a new quiz result.

        Args:
            quiz_id (UUID): The quiz answered.
            answers (Answers): The answers.
            current_user (User): The User who to authorize.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            IncompleteQuizError: If not all questions in the quiz have answers.

        Returns:
            QuizResult: The new result.
        """
        quiz = await self.check_company_member_and_quiz(
            quiz_id=quiz_id, current_user=current_user, session=session
        )

        answered = len(answers.root)
        if answered < len(quiz.questions):
            raise IncompleteQuizError

        correct_answers = [
            question["answers"][0]["correct"] for question in quiz.questions
        ]
        correct = sum(1 for x, y in zip(answers.root, correct_answers) if x == y)

        quiz_result: QuizResult = await QuizResultRepo.add_result(
            user_id=current_user.id,
            company_id=quiz.company_id,
            quiz_id=quiz_id,
            answered=answered,
            correct=correct,
            session=session,
        )

        await self.store_quiz_result(
            quiz_result=QuizResultDetails.model_validate(quiz_result)
        )
        return quiz_result

    async def get_user_rating(
        self,
        user_id: UUID,
        company_id: UUID | None = None,
        session: AsyncSession = Depends(get_session),
    ) -> float:
        """Get quiz results of one User.
        Can be used both for overall results and per company.

        Args:
            user_id (UUID): The user which to check.
            company_id (UUID | None, optional):
                The company which to check. Defaults to None.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError: If there were no results found.

        Returns:
            float: The obtained rating.
        """
        quizzes = await QuizResultRepo.get_results_by_user(
            user_id=user_id,
            company_id=company_id,
            session=session,
        )

        if not quizzes:
            raise ResultsNotFoundError(user_id)

        total_answered = sum(quiz.answered for quiz in quizzes)
        total_correct = sum(quiz.correct for quiz in quizzes)

        rating = total_correct / total_answered if total_answered > 0 else 0.0

        return rating
