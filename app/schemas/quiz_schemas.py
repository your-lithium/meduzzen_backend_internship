from uuid import UUID

from pydantic import BaseModel, ConfigDict, RootModel, field_validator, model_validator
from typing_extensions import Self


class Answer(BaseModel):
    options: dict[int, str]
    correct: list[int]

    @field_validator("options", mode="after")
    @classmethod
    def check_options_quantity(cls, options) -> Self:
        if len(options) < 2:
            raise ValueError("There must be at least two answer options.")
        return options

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
    root: list[Question]


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    description: str
    frequency: int
    questions: QuestionList


class QuestionsValidatorMixin:
    @field_validator("questions", mode="after")
    @classmethod
    def check_questions_quantity(cls, questions) -> Self:
        if questions:
            if len(questions.root) < 2:
                raise ValueError("There must be at least two questions.")
        return questions


class QuizCreateRequest(BaseModel, QuestionsValidatorMixin):
    name: str
    description: str
    frequency: int
    questions: QuestionList


class QuizUpdateRequest(BaseModel, QuestionsValidatorMixin):
    name: str | None = None
    description: str | None = None
    frequency: int | None = None
    questions: QuestionList | None = None
