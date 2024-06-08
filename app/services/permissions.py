from uuid import UUID
from app.services.exceptions import AccessDeniedError


class PermissionService:
    """Represents a service for granting permissions on actions."""

    @staticmethod
    def grant_user_permission(user_id: UUID, current_user_id: UUID, operation: str):
        if user_id != current_user_id:
            raise AccessDeniedError(
                f"You are not allowed to {operation} other users' information"
            )

    @staticmethod
    def grant_owner_permission(owner_id: UUID, current_user_id: UUID, operation: str):
        if owner_id != current_user_id:
            raise AccessDeniedError(
                f"You are not allowed to {operation} information "
                "for companies you're not an owner of"
            )
