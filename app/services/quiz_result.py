from datetime import datetime, timedelta
from uuid import UUID

import pandas as pd
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Quiz, QuizResult, StatusEnum, User
from app.db.repo.quiz_result import QuizResultRepo
from app.schemas.membership_schemas import MembershipActionRequest
from app.schemas.quiz_result_schemas import Answers, QuizResultDetails
from app.services.company import CompanyService, get_company_service
from app.services.exceptions import (
    AccessDeniedError,
    IncompleteQuizError,
    ResultsNotFoundError,
)
from app.services.membership import MembershipService, get_membership_service
from app.services.quiz import QuizService, get_quiz_service
from app.services.redis_connect import redis_client
from app.services.user import UserService, get_user_service


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

    async def retrieve_all_quiz_results(
        self,
        user_id: UUID | None = None,
        company_id: UUID | None = None,
        quiz_id: UUID | None = None,
    ) -> list[QuizResultDetails]:
        await redis_client.connect()
        keys = []
        cursor = 0

        if user_id and company_id:
            pattern = f"quiz_result:{user_id}:{company_id}:*"
        elif user_id:
            pattern = f"quiz_result:{user_id}:*"
        elif company_id:
            pattern = f"quiz_result:*:{company_id}:*"
        elif quiz_id:
            pattern = f"quiz_result:*:*:{quiz_id}:*"

        while True:
            cursor, found_keys = await redis_client.redis_client.scan(
                cursor, match=pattern
            )
            keys.extend(found_keys)
            if cursor == 0:
                break

        quiz_results = []
        for key in keys:
            data = await redis_client.get(key)
            if data:
                quiz_results.append(QuizResultDetails.model_validate_json(data))

        await redis_client.close()
        return quiz_results

    async def form_csv(
        self,
        quiz_results: list[QuizResultDetails],
        filename_prefix: str,
    ) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{filename_prefix}_{current_time}.csv"
        serialized_results = [result.model_dump() for result in quiz_results]
        df = pd.DataFrame(serialized_results)
        df.to_csv(filename, index=False)
        return filename

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

    async def get_latest_user_results(
        self,
        current_user: User,
        get_csv: bool = False,
    ) -> list[QuizResultDetails] | str:
        results = await self.retrieve_all_quiz_results(user_id=current_user.id)
        if get_csv:
            filename_prefix = str(current_user.id)
            results_csv = await self.form_csv(
                quiz_results=results, filename_prefix=filename_prefix
            )
            return results_csv
        return results

    async def get_latest_company_results(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
        get_csv: bool = False,
    ) -> list[QuizResultDetails] | str:
        await self._quiz_service.check_company_and_user(
            company_id=company_id, current_user=current_user, session=session
        )

        results = await self.retrieve_all_quiz_results(company_id=company_id)
        if get_csv:
            filename_prefix = str(company_id)
            results_csv = await self.form_csv(
                quiz_results=results, filename_prefix=filename_prefix
            )
            return results_csv
        return results

    async def get_latest_company_user_results(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
        get_csv: bool = False,
    ) -> list[QuizResultDetails] | str:
        await self._user_service.get_user_by_id(user_id=user_id, session=session)

        await self._quiz_service.check_company_and_user(
            company_id=company_id, current_user=current_user, session=session
        )

        results = await self.retrieve_all_quiz_results(
            user_id=user_id, company_id=company_id
        )
        if get_csv:
            filename_prefix = f"{company_id}_{user_id}"
            results_csv = await self.form_csv(
                quiz_results=results, filename_prefix=filename_prefix
            )
            return results_csv
        return results

    async def get_latest_quiz_results(
        self,
        quiz_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
        get_csv: bool = False,
    ) -> list[QuizResultDetails] | str:
        existing_quiz = await self._quiz_service.get_quiz_by_id(
            quiz_id=quiz_id, session=session
        )

        await self._quiz_service.check_company_and_user(
            company_id=existing_quiz.company_id,
            current_user=current_user,
            session=session,
        )

        results = await self.retrieve_all_quiz_results(quiz_id=quiz_id)
        if get_csv:
            filename_prefix = str(quiz_id)
            results_csv = await self.form_csv(
                quiz_results=results, filename_prefix=filename_prefix
            )
            return results_csv
        return results
