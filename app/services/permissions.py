from uuid import UUID

from app.services.exceptions import AccessDeniedError
from app.db.models import Membership, StatusEnum


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

    @staticmethod
    def grant_admin_permission(membership_status: StatusEnum, operation: str):
        is_admin = membership_status == StatusEnum.ADMIN

        if not is_admin:
            raise AccessDeniedError(
                f"You are not allowed to {operation} information "
                "for companies you're not an admin of"
            )

    @staticmethod
    def grant_owner_admin_permission(
        owner_id: UUID,
        membership: Membership | None,
        current_user_id: UUID,
        operation: str,
    ):
        if membership is None:
            PermissionService.grant_owner_permission(
                owner_id=owner_id, current_user_id=current_user_id, operation=operation
            )
        else:
            PermissionService.grant_admin_permission(
                membership_status=membership.status, operation=operation
            )
