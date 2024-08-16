from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logger import logger
from app.db.database import get_session
from app.db.models import Notification, NotificationStatusEnum
from app.schemas.notification_schemas import NotificationCreateRequest


class NotificationRepo:
    """Represents a repository pattern to perform CRUD on Notification model."""

    @staticmethod
    async def get_notification_by_id(
        notification_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> Notification | None:
        """Get details for one notification via its ID.

        Args:
            notification_id (UUID): The notification's ID.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Notification | None: Notification details.
        """
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalars().first()

        return notification

    @staticmethod
    async def get_notifications_by_user(
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
        result = await session.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        notifications = result.scalars().all()

        return notifications

    @staticmethod
    async def create_notification(
        notification: NotificationCreateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        """Create a new Notification.

        Args:
            notification (NotificationCreateRequest):
                The details for the new Notification.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Notification: The resulting new Notification.
        """
        logger.info("Received a notification creation request")

        new_notification = Notification(
            user_id=notification.user_id,
            status=NotificationStatusEnum.UNREAD,
            text=notification.text,
        )

        session.add(new_notification)
        await session.commit()
        await session.refresh(new_notification)

        logger.info("New notification created successfully")
        return new_notification

    @staticmethod
    async def update_notification_status(
        existing_notification: Notification,
        notification_status: NotificationStatusEnum,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        """Mark a Notification as either read or unread.

        Args:
            existing_notification (Notification): The Notification to alter.
            notification_status (NotificationStatusEnum): The status to set.
            session (AsyncSession):
                The database session used for querying.
                Defaults to the session obtained through get_session.

        Returns:
            Notification: The updated Notification.
        """
        logger.info(
            f"Received request to update status of notification with "
            f"ID {existing_notification.id}"
        )

        setattr(existing_notification, "status", notification_status)

        await session.commit()
        await session.refresh(existing_notification)

        logger.info(
            f"Notification with ID {existing_notification.id} updated successfully"
        )
        return existing_notification
