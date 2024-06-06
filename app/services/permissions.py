from uuid import UUID
from app.services.exceptions import AccessDeniedError


class PermissionService:
    """Represents a service for granting permissions on actions."""

    @staticmethod
    def grant_user_update_permission(user_id: UUID, current_user_id: UUID):
        if user_id != current_user_id:
            raise AccessDeniedError(
                "You are not allowed to update other users' information"
            )

    @staticmethod
    def grant_user_delete_permission(user_id: UUID, current_user_id: UUID):
        if user_id != current_user_id:
            raise AccessDeniedError("You are not allowed to delete other users")
