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


class IncorrectPasswordError(BaseError):
    def __init__(self):
        super().__init__("Incorrect password provided")

    def errors(self):
        return "Incorrect password provided"


class UnauthorizedError(BaseError):
    def __init__(self, message: str = "Invalid authentication credentials"):
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
    def __init__(self, message: str = "Access denied"):
        self.message = message
        super().__init__(self.message)

    def errors(self):
        return self.message
