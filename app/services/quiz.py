from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Company, Membership, Quiz, User
from app.db.repo.quiz import QuizRepo
from app.schemas.membership_schemas import MembershipActionRequest
from app.schemas.quiz_schemas import QuizCreateRequest, QuizUpdateRequest
from app.services.company import CompanyService, get_company_service
from app.services.exceptions import MembershipNotFoundError, QuizNotFoundError
from app.services.membership import MembershipService, get_membership_service
from app.services.permissions import PermissionService
from app.services.user import UserService, get_user_service


def get_quiz_service(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    membership_service=Depends(get_membership_service),
):
    return QuizService(user_service, company_service, membership_service)


class QuizService:
    """Represents a service for handling requests to Quiz model."""

    def __init__(
        self,
        user_service: UserService,
        company_service: CompanyService,
        membership_service: MembershipService,
    ) -> None:
        self._user_service = user_service
        self._company_service = company_service
        self._membership_service = membership_service

    async def check_company_and_user(
        self,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Check if a Company exists and if a User is its owner or admin.

        Args:
            company_id (UUID): The ID of a Company to check.
            current_user (User): The User to check.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
        existing_company = await self._company_service.get_company_by_id(
            company_id=company_id, session=session
        )

        parties = MembershipActionRequest(
            company_id=company_id, user_id=current_user.id
        )
        membership: Membership | None = None
        try:
            membership = await self._membership_service.get_membership_by_parties(
                parties=parties, session=session
            )
        except MembershipNotFoundError:
            pass
        finally:
            PermissionService.grant_owner_admin_permission(
                owner_id=existing_company.owner_id,
                membership=membership,
                current_user_id=current_user.id,
                operation="update quiz",
            )

    async def get_quizzes_by_company(
        self,
        company_id: UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Quiz]:
        """Get a list of quizzes belonging to one Company.

        Args:
            company_id (UUID): The ID of the company to check.
            limit (int, optional): How much quizzes to get. Defaults to 10.
            offset (int, optional): Where to start getting quizzes. Defaults to 0.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Quiz]: The list of quizzes.
        """
        quizzes: list[Quiz] = await QuizRepo.get_quizzes_by_company(
            company_id=company_id,
            limit=limit,
            offset=offset,
            session=session,
        )
        return quizzes

    async def get_quiz_by_id(
        self,
        quiz_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        """Get details for one quiz via its ID.

        Args:
            quiz_id (UUID): The quiz's ID.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Raises:
            QuizNotFoundError: If there's no Quiz with given ID.

        Returns:
            Quiz: Quiz details.
        """
        quiz: Quiz | None = await QuizRepo.get_by_id(record_id=quiz_id, session=session)

        if quiz is None:
            raise QuizNotFoundError(quiz_id)

        return quiz

    async def create_quiz(
        self,
        quiz: QuizCreateRequest,
        company_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Quiz:
        """Create a new quiz.

        Args:
            quiz (QuizCreateRequest): Details for creating a new quiz.
            company_id (UUID): The company which the quiz should belong to.
            current_user (User): The current user to authorize as an owner or admin.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Quiz: Details of the new quiz.
        """
        await self.check_company_and_user(
            company_id=company_id,
            current_user=current_user,
            session=session,
        )

        new_quiz: Quiz = await QuizRepo.create_quiz(
            quiz=quiz, company_id=company_id, session=session
        )
        return new_quiz

    async def update_quiz(
        self,
        quiz_id: UUID,
        quiz_update: QuizUpdateRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
        """Update an existing quiz.

        Args:
            quiz_id (UUID): The ID of the quiz to update.
            quiz_update (QuizUpdateRequest): The details which to update in a quiz.
            current_user (User): The current user to authorize as an owner or admin.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Company: Details of the updated quiz.
        """
        existing_quiz = await self.get_quiz_by_id(quiz_id=quiz_id, session=session)

        await self.check_company_and_user(
            company_id=existing_quiz.company_id,
            current_user=current_user,
            session=session,
        )

        updated_quiz: Quiz = await QuizRepo.update_quiz(
            existing_quiz=existing_quiz,
            quiz_update=quiz_update,
            session=session,
        )

        return updated_quiz

    async def delete_quiz(
        self,
        quiz_id: UUID,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> None:
        """Delete a quiz.

        Args:
            quiz_id (UUID): The ID of the quiz to delete.
            current_user (User): The current user to authorize as an owner or admin.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.
        """
        quiz: Quiz = await self.get_quiz_by_id(quiz_id=quiz_id, session=session)

        await self.check_company_and_user(
            company_id=quiz.company_id,
            current_user=current_user,
            session=session,
        )

        await QuizRepo.delete(entity=quiz, session=session)
