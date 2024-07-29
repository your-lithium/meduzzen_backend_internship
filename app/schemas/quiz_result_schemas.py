from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, RootModel


class QuizResultDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    company_id: UUID
    quiz_id: UUID
    time: datetime
    answered: int
    correct: int


class Answers(RootModel):
    root: list[list[int]]


class MeanScore(RootModel):
    root: float
