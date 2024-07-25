from pydantic import BaseModel, ConfigDict
from uuid import UUID

from app.db.models import StatusEnum


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    user_id: UUID
    status: StatusEnum


class MembershipActionRequest(BaseModel):
    company_id: UUID
    user_id: UUID
