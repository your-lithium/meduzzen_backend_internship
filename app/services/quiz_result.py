from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Quiz, QuizResult, StatusEnum, User
from app.db.repo.quiz_result import QuizResultRepo
from app.schemas.membership_schemas import MembershipActionRequest
from app.schemas.quiz_result_schemas import (
    Answers,
    LatestQuizAnswer,
    MeanScoreTimed,
    QuizResultDetails,
    UserLatestQuizAnswers,
    UserMeanScoreTimed,
)
from app.services.company import CompanyService, get_company_service
from app.services.exceptions import (
    AccessDeniedError,
    IncompleteQuizError,
    ResultsNotFoundError,
)
from app.services.membership import MembershipService, get_membership_service
from app.services.notification import NotificationService, get_notification_service
from app.services.quiz import QuizService, get_quiz_service
from app.services.user import UserService, get_user_service
from app.utils.redis import redis_client


def get_quiz_result_service(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    membership_service=Depends(get_membership_service),
    quiz_service=Depends(get_quiz_service),
    notification_service=Depends(get_notification_service),
):
    return QuizResultService(
        user_service,
        company_service,
        membership_service,
        quiz_service,
        notification_service,
    )


class QuizResultService:
    """Represents a service for handling requests to QuizResult model."""

    def __init__(
        self,
        user_service: UserService,
        company_service: CompanyService,
        membership_service: MembershipService,
        quiz_service: QuizService,
        notification_service: NotificationService,
    ) -> None:
        self._user_service = user_service
        self._company_service = company_service
        self._membership_service = membership_service
        self._quiz_service = quiz_service
        self._notification_service = notification_service

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
        """Store a quiz result in Redis DB.

        Args:
            quiz_result (QuizResultDetails): The quiz result to store.
        """
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
        """Retrieve all relevant quiz results stored in Redis DB.
        Can be use for one User, one Company, one Quiz, or a User-Company pair.

        Args:
            user_id (UUID | None, optional):
                The User for whom to retrieve data. Defaults to None.
            company_id (UUID | None, optional):
                The Company for which to retrieve data. Defaults to None.
            quiz_id (UUID | None, optional):
                The Quiz for which to retrieve data. Defaults to None.

        Returns:
            list[QuizResultDetails]: The retrieved data.
        """
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
        """Form a save a comma-separated value file with QuizResults.

        Args:
            quiz_results (list[QuizResultDetails]): The data which to save.
            filename_prefix (str): The prefix for the filename.

        Returns:
            str: The resulting filename.
        """
        current_time = datetime.now(ZoneInfo("Europe/Kyiv")).strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
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

    async def calculate_rating(
        self,
        results: list[QuizResult],
    ) -> float:
        """Calculate a rating float from a list of QuizResults.

        Args:
            quizzes (list[QuizResult]): The results to calculate.

        Returns:
            float: The calculated rating.
        """
        total_answered = sum(result.answered for result in results)
        total_correct = sum(result.correct for result in results)

        rating = total_correct / total_answered if total_answered > 0 else 0.0

        return rating

    async def get_user_rating(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> float:
        """Get rating of one User.

        Args:
            user_id (UUID): The user which to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError: If there were no results found.

        Returns:
            float: The obtained rating.
        """
        results = await QuizResultRepo.get_results_by_user(
            user_id=user_id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(user_id)

        rating = await self.calculate_rating(results=results)

        return rating

    async def get_user_company_rating(
        self,
        user_id: UUID,
        company_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> float:
        """Get quiz results of one User in one Company.

        Args:
            user_id (UUID): The user which to check.
            company_id (UUID): The company which to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError: If there were no results found.

        Returns:
            float: The obtained rating.
        """
        results = await QuizResultRepo.get_results_by_parties(
            user_id=user_id,
            company_id=company_id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(user_id)

        rating = await self.calculate_rating(results=results)

        return rating

    async def get_latest_user_results(
        self,
        current_user: User,
        get_csv: bool = False,
    ) -> list[QuizResultDetails] | str:
        """Get the latest results of one User from the Redis DB.

        Args:
            current_user (User): The User which to get the info for.
            get_csv (bool, optional):
                Whether or not to save the results to a CSV file. Defaults to False.

        Returns:
            list[QuizResultDetails] | str: The obtained results.
        """
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
        get_csv: bool = False,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResultDetails] | str:
        """Get the latest results of one Company from the Redis DB.

        Args:
            company_id (UUID): The Company which to get the info for.
            current_user (User): The User to authorize.
            get_csv (bool, optional):
                Whether or not to save the results to a CSV file. Defaults to False.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResultDetails] | str: The obtained results.
        """
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
        get_csv: bool = False,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResultDetails] | str:
        """Get the latest results of one User in one Company from the Redis DB.

        Args:
            company_id (UUID): The Company which to get the info for.
            user_id (UUID): The User which to get the info for.
            current_user (User): The User to authorize.
            get_csv (bool, optional):
                Whether or not to save the results to a CSV file. Defaults to False.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResultDetails] | str: The obtained results.
        """
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
        get_csv: bool = False,
        session: AsyncSession = Depends(get_session),
    ) -> list[QuizResultDetails] | str:
        """Get the latest results of one Quiz from the Redis DB.

        Args:
            quiz_id (UUID): The Quiz which to get the info for.
            current_user (User): The User to authorize.
            get_csv (bool, optional):
                Whether or not to save the results to a CSV file. Defaults to False.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[QuizResultDetails] | str: The obtained results.
        """
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

    async def find_latest_answers(
        self, all_results: list[QuizResult]
    ) -> list[LatestQuizAnswer]:
        """Helper function to find the latest answers for each quiz answered.

        Args:
            all_results (list[QuizResult]): All of the quiz results.

        Returns:
            list[LatestQuizAnswer]: The resulting list of latest answers.
        """
        latest_answers_dict: dict[UUID, QuizResult] = {}
        for answer in all_results:
            if (
                answer.quiz_id not in latest_answers_dict
                or answer.time > latest_answers_dict[answer.quiz_id].time
            ):
                latest_answers_dict[answer.quiz_id] = answer

        latest_answers = [
            LatestQuizAnswer(quiz_id=quiz_id, time=answer.time)
            for quiz_id, answer in latest_answers_dict.items()
        ]

        return latest_answers

    async def calculate_dynamics(
        self,
        results: list[QuizResult],
    ) -> list[MeanScoreTimed]:
        """Calculate the changes in rating over time.

        Args:
            results (list[QuizResult]): The results which to calculate the dynamics for.

        Returns:
            list[MeanScoreTimed]: The calculated dynamics.
        """
        results.sort(key=lambda result: result.time)

        mean_scores_timed = []
        processed_quizzes = []
        for result in results:
            processed_quizzes.append(result)
            mean_score = MeanScoreTimed(
                time=result.time,
                mean_score=await self.calculate_rating(processed_quizzes),
            )
            mean_scores_timed.append(mean_score)

        return mean_scores_timed

    async def get_user_dynamics(
        self,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> list[MeanScoreTimed]:
        """Calculate the changes of one User's rating over time.

        Args:
            current_user (User): The User which to calculate the dynamics for.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError: If the User hasn't completed any quizzes.

        Returns:
            list[MeanScoreTimed]: The calculated dynamics.
        """
        results = await QuizResultRepo.get_results_by_user(
            user_id=current_user.id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(current_user.id)

        mean_scores_timed = await self.calculate_dynamics(results=results)
        return mean_scores_timed

    async def get_current_user_latest_answers(
        self,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> list[LatestQuizAnswer]:
        """Get the latest times a User has completed any quiz they've taken before.

        Args:
            current_user (User): The User whom to get the data for.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError: If the User hasn't completed any quizzes.

        Returns:
            list[LatestQuizAnswer]: The resulting times for each quiz.
        """
        all_answers = await QuizResultRepo.get_results_by_user(
            user_id=current_user.id,
            session=session,
        )

        if not all_answers:
            raise ResultsNotFoundError(current_user.id)

        latest_answers = await self.find_latest_answers(all_results=all_answers)

        return latest_answers

    async def get_company_dynamics(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> list[UserMeanScoreTimed]:
        """Calculate the changes in ratings of all Users that've taken quizzes
        in a Company. Only accounts for the Quizzes of this one Company.

        Args:
            company_id (UUID): The Company which to calculate ratings for.
            current_user (User): The User to authorize.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError:
                If there aren't any quizzes completed for the Company.

        Returns:
            list[UserMeanScoreTimed]: The resulting dynamics for each User.
        """
        await self._quiz_service.check_company_and_user(
            company_id=company_id, current_user=current_user, session=session
        )

        results = await QuizResultRepo.get_results_by_company(
            company_id=company_id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(current_user.id)

        user_results = defaultdict(list)
        for result in results:
            user_results[result.user_id].append(result)

        user_mean_scores_timed = [
            UserMeanScoreTimed(
                user_id=user_id,
                scores=await self.calculate_dynamics(results=result_list),
            )
            for user_id, result_list in user_results.items()
        ]

        return user_mean_scores_timed

    async def get_company_member_dynamics(
        self,
        company_id: UUID,
        user_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> list[MeanScoreTimed]:
        """Calculate the changes in ratings of one User in a Company.
        Only accounts for the Quizzes of this one Company.

        Args:
            company_id (UUID): The Company which to calculate ratings for.
            user_id (UUID): The User which to calculate ratings for.
            current_user (User): The User to authorize.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError:
                If the User hasn't completed any quizzes in a Company.

        Returns:
            list[UserMeanScoreTimed]: The resulting dynamics for the User.
        """
        await self._user_service.get_user_by_id(user_id=user_id, session=session)
        await self._quiz_service.check_company_and_user(
            company_id=company_id, current_user=current_user, session=session
        )

        results = await QuizResultRepo.get_results_by_user(
            user_id=user_id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(user_id)

        mean_scores_timed = await self.calculate_dynamics(results=results)
        return mean_scores_timed

    async def get_company_latest_answers(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> list[UserLatestQuizAnswers]:
        """Get the latest times each User has answered any Quiz of the Company.

        Args:
            company_id (UUID): The Company which to retrieve the information for.
            current_user (User): The User to authorize.
            session (AsyncSession, optional):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            ResultsNotFoundError:
                If there aren't any quizzes completed for the Company.

        Returns:
            list[UserLatestQuizAnswers]: The resulting latest answers for each User.
        """
        await self._quiz_service.check_company_and_user(
            company_id=company_id, current_user=current_user, session=session
        )

        results = await QuizResultRepo.get_results_by_company(
            company_id=company_id,
            session=session,
        )

        if not results:
            raise ResultsNotFoundError(current_user.id)

        user_results: dict[UUID, list] = {}
        for result in results:
            user_results.setdefault(result.user_id, []).append(result)

        latest_answers = []
        for user_id, user_result_list in user_results.items():
            user_latest_answers = await self.find_latest_answers(
                all_results=user_result_list
            )

            latest_answers.append(
                UserLatestQuizAnswers(
                    user_id=user_id, latest_answers=user_latest_answers
                )
            )

        return latest_answers

    async def check_quiz_schedule(
        self,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        now = datetime.now(ZoneInfo("Europe/Kyiv"))

        companies = await self._company_service.get_all_companies(
            limit=None, offset=0, session=session
        )

        for company in companies:
            owner = await self._user_service.get_user_by_id(
                user_id=company.owner_id, session=session
            )
            members = await self._membership_service.get_members_by_company(
                company_id=company.id, session=session
            )

            quizzes = await self._quiz_service.get_quizzes_by_company(
                company_id=company.id, limit=None, offset=0, session=session
            )

            company_latest_answers = await self.get_company_latest_answers(
                company_id=company.id, current_user=owner, session=session
            )

            for member in members:
                latest_answers: UserLatestQuizAnswers | None = next(
                    (
                        answer
                        for answer in company_latest_answers
                        if answer.user_id == member.id
                    ),
                    None,
                )

                if latest_answers:
                    for quiz in quizzes:
                        latest_answer: LatestQuizAnswer | None = next(
                            (
                                answer
                                for answer in latest_answers.latest_answers
                                if answer.quiz_id == quiz.id
                            ),
                            None,
                        )

                        if latest_answer:
                            days_gone = (now - latest_answer.time).days
                            if days_gone >= quiz.frequency:
                                await self._notification_service.send_notification(
                                    user_id=member.id,
                                    text=str(
                                        f"You haven't taken quiz {quiz.id} from "
                                        f"company {company.id} in a long time. "
                                        "Please take it."
                                    ),
                                    session=session,
                                )
                        else:
                            await self._notification_service.send_notification(
                                user_id=member.id,
                                text=str(
                                    f"You haven't ever taken quiz {quiz.id} from "
                                    f"company {company.id}. Please take it."
                                ),
                                session=session,
                            )
                else:
                    for quiz in quizzes:
                        await self._notification_service.send_notification(
                            user_id=member.id,
                            text=str(
                                f"You haven't ever taken quiz {quiz.id} from "
                                f"company {company.id}. Please take it."
                            ),
                            session=session,
                        )
