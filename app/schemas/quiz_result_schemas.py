from pydantic import BaseModel, RootModel
from uuid import UUID
from datetime import datetime


class QuizResultDetails(BaseModel):
    user_id: UUID
    company_id: UUID
    quiz_id: UUID
    time: datetime
    answered: int
    correct: int

    class Config:
        from_attributes = True


class Answers(RootModel):
    root: list[list[int]]


class MeanScore(RootModel):
    root: float
