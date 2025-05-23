from typing import Any

from pydantic import EmailStr


class BaseError(Exception):
    pass


class ObjectNotFoundError(BaseError):
    def __init__(self, identifier: Any, model_name: str) -> None:
        self.identifier = identifier
        self.model_name = model_name
        super().__init__(f"{model_name} with given identifier - {identifier} not found")


class UserNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "user"):
        super().__init__(identifier, model_name)

    def errors(self):
        return f"{self.model_name} with given identifier - {self.identifier} not found"


class CompanyNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "company"):
        super().__init__(identifier, model_name)

    def errors(self):
        return f"{self.model_name} with given identifier - {self.identifier} not found"


class MembershipNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "membership"):
        super().__init__(identifier, model_name)

    def errors(self):
        return f"{self.model_name} with given identifier - {self.identifier} not found"


class QuizNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "quiz"):
        super().__init__(identifier, model_name)

    def errors(self):
        return f"{self.model_name} with given identifier - {self.identifier} not found"


class ResultsNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "quiz result for user"):
        super().__init__(identifier, model_name)

    def errors(self):
        return (
            f"{self.model_name} for user with given identifier - "
            f"{self.identifier} not found"
        )


class NotificationNotFoundError(ObjectNotFoundError):
    def __init__(self, identifier: Any, model_name: str = "notification"):
        super().__init__(identifier, model_name)

    def errors(self):
        return f"{self.model_name} with given identifier - {self.identifier} not found"


class ObjectAlreadyExistsError(BaseError):
    def __init__(self, object_value: Any, object_name: str, model_name: str) -> None:
        self.object_value = object_value
        self.object_name = object_name
        self.model_name = model_name
        super().__init__(
            f"{self.model_name} with given unique {self.object_name} - "
            f"{self.object_value} already taken"
        )

    def errors(self):
        return (
            f"{self.model_name} with given unique {self.object_name} - "
            f"{self.object_value} already taken"
        )


class EmailAlreadyExistsError(ObjectAlreadyExistsError):
    def __init__(
        self,
        object_value: EmailStr,
        object_name: str = "email",
        model_name: str = "user",
    ) -> None:
        super().__init__(object_value, object_name, model_name)


class UsernameAlreadyExistsError(ObjectAlreadyExistsError):
    def __init__(
        self, object_value: str, object_name: str = "username", model_name: str = "user"
    ) -> None:
        super().__init__(object_value, object_name, model_name)


class CompanyNameAlreadyExistsError(ObjectAlreadyExistsError):
    def __init__(
        self, object_value: str, object_name: str = "name", model_name: str = "company"
    ) -> None:
        super().__init__(object_value, object_name, model_name)


class MembershipAlreadyExistsError(ObjectAlreadyExistsError):
    def __init__(
        self,
        object_value: str,
        object_name: str = "link",
        model_name: str = "membership",
    ) -> None:
        super().__init__(object_value, object_name, model_name)


class IncorrectPasswordError(BaseError):
    def __init__(self):
        super().__init__("Incorrect password provided")

    def errors(self):
        return "Incorrect password provided"


class UnauthorizedError(BaseError):
    def __init__(
        self, message: str | tuple[str, ...] = "Invalid authentication credentials"
    ):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message


class InactiveUserError(BaseError):
    def __init__(self):
        super().__init__("Inactive user")

    def errors(self):
        return "Inactive user"


class AccessDeniedError(BaseError):
    def __init__(self, message: str | tuple[str, ...] = "Access denied"):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message


class IncompleteQuizError(BaseError):
    def __init__(
        self,
        message: str | tuple[str, ...] = "You must answer all questions in the quiz",
    ):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message


class InvalidPaginationParameterError(BaseError):
    def __init__(
        self,
        message: (
            str | tuple[str, ...]
        ) = "Pagination parameters (limit and offset) cannot be negative",
    ):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message


class UnsupportedFileFormatError(BaseError):
    def __init__(
        self,
        message: str | tuple[str, ...] = (
            "File format not supported. Must be xls, xlsx, xlsm, xlsb, odf, ods or odt"
        ),
    ):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message
