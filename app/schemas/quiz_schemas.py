from pydantic import BaseModel, model_validator
from uuid import UUID
from typing_extensions import Self


class Question(BaseModel):
    question: str
    options: dict[int, str]
    correct: list[int]

    @model_validator(mode="after")
    def check_options_quantity(self) -> Self:
        if len(self.options) < 2:
            raise ValueError("There must be at least two answer options.")
        return self

    @model_validator(mode="after")
    def check_correctss_quantity(self) -> Self:
        if len(self.correct) < 1:
            raise ValueError("There must be at least one correct answer.")
        elif len(self.correct) == len(self.options):
            raise ValueError("There must be at least one incorrect answer.")
        elif len(self.correct) > len(self.options):
            raise ValueError(
                "There can't be more correct options than options in general."
            )
        return self

    @model_validator(mode="after")
    def check_options_difference(self) -> Self:
        if len(self.options) > len(set(self.options.values())):
            raise ValueError("Answer options must be unique.")
        return self

    def to_dict(self):
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class QuizResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: str
    frequency: int
    questions: list[Question]

    class Config:
        from_attributes = True


class QuizCreateRequest(BaseModel):
    name: str
    description: str
    frequency: int
    questions: list[Question]

    @model_validator(mode="after")
    def check_questions_quantity(self) -> Self:
        if len(self.questions) < 2:
            raise ValueError("There must be at least two questions.")
        return self


class QuizUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    frequency: int | None = None
    questions: list[Question] | None = None

    @model_validator(mode="after")
    def check_questions_quantity(self) -> Self:
        if self.questions:
            if len(self.questions) < 2:
                raise ValueError("There must be at least two questions.")
        return self
