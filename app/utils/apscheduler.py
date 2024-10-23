from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.database import AsyncSessionLocal
from app.services.company import CompanyService
from app.services.membership import MembershipService
from app.services.notification import NotificationService
from app.services.quiz import QuizService
from app.services.quiz_result import get_quiz_result_service
from app.services.user import UserService

jobstores = {"default": MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstores=jobstores)


@scheduler.scheduled_job("cron", day_of_week="mon-sun", hour=0, minute=0, second=0)
async def scheduled_job():
    user_service = UserService()
    company_service = CompanyService()
    membership_service = MembershipService(user_service, company_service)
    notification_service = NotificationService()
    quiz_service = QuizService(
        user_service, company_service, membership_service, notification_service
    )
    quiz_result_service = get_quiz_result_service(
        user_service,
        company_service,
        membership_service,
        quiz_service,
        notification_service,
    )
    session = AsyncSessionLocal()
    await quiz_result_service.check_quiz_schedule(session=session)
