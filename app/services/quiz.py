from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.models import Company, User, Quiz
from app.schemas.quiz_schemas import QuizCreateRequest, QuizUpdateRequest
from app.db.repo.quiz import QuizRepo
from app.services.exceptions import QuizNotFoundError
from app.db.database import get_session
from app.services.permissions import PermissionService
from app.services.company import get_company_service, CompanyService
from app.services.user import get_user_service, UserService
from app.services.membership import get_membership_service, MembershipService


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
        existing_company = await self._company_service.get_company_by_id(
            company_id=company_id, session=session
        )

        admins = await self._membership_service.get_admins_by_company(
            company_id=existing_company.id,
            limit=None,
            session=session,
        )
        admin_ids = [admin.id for admin in admins]

        PermissionService.grant_owner_admin_permission(
            owner_id=existing_company.owner_id,
            admin_ids=admin_ids,
            current_user_id=current_user.id,
            operation="update quiz",
        )

    async def get_quizzes_by_company(
        self,
        company_id=UUID,
        limit: int = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[Quiz]:
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
        quiz: Quiz | None = await QuizRepo.get_quiz_by_id(
            quiz_id=quiz_id, session=session
        )

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
        await self.check_company_and_user(
            company_id=company_id,
            current_user=current_user,
            session=session,
        )

        quiz: Quiz | None = await QuizRepo.create_quiz(
            quiz=quiz, company_id=company_id, session=session
        )

        return quiz

    async def update_quiz(
        self,
        quiz_id: UUID,
        quiz_update: QuizUpdateRequest,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Company:
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
        quiz: Quiz | None = await self.get_quiz_by_id(quiz_id=quiz_id, session=session)

        await self.check_company_and_user(
            company_id=quiz.company_id,
            current_user=current_user,
            session=session,
        )

        await QuizRepo.delete_quiz(quiz=quiz, session=session)
