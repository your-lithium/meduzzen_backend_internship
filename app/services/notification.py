from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Notification, NotificationStatusEnum, User
from app.db.repo.notification import NotificationRepo
from app.schemas.notification_schemas import NotificationCreateRequest
from app.services.permissions import PermissionService


def get_notification_service():
    return NotificationService()


class NotificationService:
    """Represents a service for handling requests to Notification model."""

    async def get_notifications_by_user(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[Notification]:
        notifications = await NotificationRepo.get_notifications_by_user(
            user_id=user_id, session=session
        )
        return notifications

    async def send_notification(
        self,
        user_id: UUID,
        text: str,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        notification = NotificationCreateRequest(user_id=user_id, text=text)
        notification: Notification = await NotificationRepo.create_notification(
            notification=notification, session=session
        )
        return notification

    async def update_notification_status(
        self,
        notification_id: UUID,
        notification_status: NotificationStatusEnum,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        existing_notification: Notification = (
            await NotificationRepo.get_notification_by_id(
                notification_id=notification_id, session=session
            )
        )

        PermissionService.grant_user_permission(
            user_id=existing_notification.user_id,
            current_user_id=current_user.id,
            operation="update",
        )

        updated_notification: Notification = (
            await NotificationRepo.update_notification_status(
                existing_notification=existing_notification,
                notification_status=notification_status,
                session=session,
            )
        )
        return updated_notification
