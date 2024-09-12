from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Notification, NotificationStatusEnum, User
from app.db.repo.notification import NotificationRepo
from app.schemas.notification_schemas import NotificationCreateRequest
from app.services.exceptions import NotificationNotFoundError
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
        """Get the notifications left for the specific User.

        Args:
            user_id (UUID): The User for whom to retrieve notifications.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            list[Notification]: The list of retrieved Notifications.
        """
        notifications = await NotificationRepo.get_notifications_by_user(
            user_id=user_id, session=session
        )
        return notifications

    async def send_notification(
        self,
        user_id: UUID,
        text: str | tuple[str, ...],
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        """Create a new Notification.

        Args:
            user_id (UUID): The User the new Notification is intended for.
            text (str): The text of the new Notification.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Notification: The resulting new Notification.
        """
        notification = NotificationCreateRequest(user_id=user_id, text=text)
        new_notification: Notification = await NotificationRepo.create_notification(
            notification=notification, session=session
        )
        return new_notification

    async def update_notification_status(
        self,
        notification_id: UUID,
        notification_status: NotificationStatusEnum,
        current_user: User,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        """Mark a Notification as either read or unread.

        Args:
            notification_id (UUID): The ID of the Notification to alter.
            notification_status (NotificationStatusEnum): The status to set.
            current_user (User): The User to autorize.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Notification: The updated Notification.
        """
        existing_notification: Notification | None = await NotificationRepo.get_by_id(
            record_id=notification_id, session=session
        )

        if not existing_notification:
            raise NotificationNotFoundError(identifier=notification_id)

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
