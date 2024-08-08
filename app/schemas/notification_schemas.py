from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import NotificationStatusEnum


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    time: datetime
    status: NotificationStatusEnum
    text: str


class NotificationCreateRequest(BaseModel):
    user_id: UUID
    text: str
