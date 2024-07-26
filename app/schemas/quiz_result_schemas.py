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

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "company_id": str(self.company_id),
            "quiz_id": str(self.quiz_id),
            "time": self.time.isoformat(),
            "answered": self.answered,
            "correct": self.correct,
        }


class Answers(RootModel):
    root: list[list[int]]


class MeanScore(RootModel):
    root: float
