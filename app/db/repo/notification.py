from typing import Type
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Notification, NotificationStatusEnum
from app.db.repo.base import BaseRepo
from app.schemas.notification_schemas import (
    NotificationCreateRequest,
    NotificationUpdateRequest,
)


class NotificationRepo(BaseRepo[Notification]):
    """Represents a repository pattern to perform CRUD on Notification model."""

    @classmethod
    def get_model(cls) -> Type[Notification]:
        return Notification

    @staticmethod
    async def get_notifications_by_user(
        user_id: UUID,
        session: AsyncSession = Depends(get_session),
    ) -> list[Notification]:
        return await NotificationRepo.get_all_by_fields(
            fields=[Notification.user_id],
            values=[user_id],
            limit=None,
            offset=0,
            session=session,
        )

    @staticmethod
    async def create_notification(
        notification: NotificationCreateRequest,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        new_notification = Notification(
            user_id=notification.user_id,
            status=NotificationStatusEnum.UNREAD,
            text=notification.text,
        )
        return await NotificationRepo.create(entity=new_notification, session=session)

    @staticmethod
    async def bulk_create_notifications(
        notifications: list[NotificationCreateRequest],
        session: AsyncSession = Depends(get_session),
    ) -> list[Notification]:
        new_notifications = [
            {
                "user_id": notification.user_id,
                "status": NotificationStatusEnum.UNREAD,
                "text": notification.text,
            }
            for notification in notifications
        ]
        return await NotificationRepo.bulk_create(
            entities=new_notifications, session=session
        )

    @staticmethod
    async def update_notification_status(
        existing_notification: Notification,
        notification_status: NotificationStatusEnum,
        session: AsyncSession = Depends(get_session),
    ) -> Notification:
        notification_update = NotificationUpdateRequest(status=notification_status)
        update_data = notification_update.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        return await NotificationRepo.update(
            entity=existing_notification, update_data=update_data, session=session
        )
