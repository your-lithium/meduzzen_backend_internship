from pydantic import BaseModel, ConfigDict
from uuid import UUID


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    owner_id: UUID
    is_public: bool


class CompanyCreateRequest(BaseModel):
    name: str
    description: str
    is_public: bool


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
