from pydantic import BaseModel
from uuid import UUID

from app.db.models import StatusEnum


class MembershipResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    status: StatusEnum

    class Config:
        from_attributes = True


class MembershipActionRequest(BaseModel):
    company_id: UUID
    user_id: UUID
