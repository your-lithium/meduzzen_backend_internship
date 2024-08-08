from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import NotificationStatusEnum, User
from app.schemas.notification_schemas import NotificationResponse
from app.services.auth import get_current_user
from app.services.notification import (NotificationService,
                                       get_notification_service)

router = APIRouter(prefix="/notifications", tags=["Notification Methods"])


@router.get("/me", response_model=list[NotificationResponse])
async def get_current_user_notifications(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
    session: AsyncSession = Depends(get_session),
):
    notifications = await notification_service.get_notifications_by_user(
        user_id=current_user.id, session=session
    )
    return notifications


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification_status(
    notification_id: UUID,
    notification_status: NotificationStatusEnum,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
    session: AsyncSession = Depends(get_session),
):
    notification = await notification_service.update_notification_status(
        notification_id=notification_id,
        notification_status=notification_status,
        current_user=current_user,
        session=session,
    )
    return notification
