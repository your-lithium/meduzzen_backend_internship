from pydantic import BaseModel
from uuid import UUID


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    is_public: bool

    class Config:
        from_attributes = True


class CompanyCreateRequest(BaseModel):
    name: str
    description: str
    is_public: bool


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
