from pydantic import BaseModel, RootModel, ConfigDict
from uuid import UUID
from datetime import datetime


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
