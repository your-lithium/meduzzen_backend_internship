from typing import Any


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
        

class ValidationError(BaseError):
    def __init__(self, message: str, field_errors: dict[str, Any] = None) -> None:
        self.field_errors = field_errors if field_errors is not None else {}
        super().__init__(message)

    def __str__(self) -> str:
        base_message = super().__str__()
        if self.field_errors:
            field_errors_str = "; ".join([f"{field}: {error}" for field, error in self.field_errors.items()])
            return f"{base_message} (Field errors: {field_errors_str})"
        return base_message
 

class UserAlreadyExistsError(BaseError):
    def __init__(self) -> None:
        super().__init__(f"User with the same username or email already exists")
    
    def errors(self):
        return "User with the same username or email already exists"
        