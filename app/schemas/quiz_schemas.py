from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)
from typing_extensions import Self


class Answer(BaseModel):
    options: dict[int, str] = Field(
        ..., min_length=2, examples=[{0: "option 1", 1: "option 2"}]
    )
    correct: list[int]

    @model_validator(mode="after")
    @classmethod
    def check_corrects_quantity(cls, values):
        correct = values.correct
        options = values.options

        if len(correct) < 1:
            raise ValueError("There must be at least one correct answer.")
        elif len(correct) == len(options):
            raise ValueError("There must be at least one incorrect answer.")
        elif len(correct) > len(options):
            raise ValueError(
                "There can't be more correct options than options in general."
            )

        return values

    @field_validator("options", mode="after")
    @classmethod
    def check_options_difference(cls, options) -> Self:
        if len(options) > len(set(options.values())):
            raise ValueError("Answer options must be unique.")
        return options


class AnswerList(RootModel):
    root: list[Answer]


class Question(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    answers: AnswerList


class QuestionList(RootModel):
    root: list[Question] = Field(..., min_length=2)


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    description: str
    frequency: int
    questions: QuestionList


class QuizCreateRequest(BaseModel):
    name: str
    description: str
    frequency: int
    questions: QuestionList


class QuizUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    frequency: int | None = None
    questions: QuestionList | None = None
