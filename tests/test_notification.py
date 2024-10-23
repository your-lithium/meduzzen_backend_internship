from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, NotificationStatusEnum
from app.db.repo.notification import NotificationRepo
from tests import payload
from tests.conftest import assert_real_matches_expected, get_user_and_company_ids


@pytest.mark.asyncio
async def test_get_current_user_notifications(
    fill_db_with_notifications, client: AsyncClient, test_session: AsyncSession
):
    time = datetime.now(ZoneInfo("Europe/Kyiv"))
    user_id, _ = await get_user_and_company_ids(
        user_email=payload.test_user_1.email, session=test_session
    )
    assert user_id is not None, "User not found"

    response = await client.get("/notifications/me")
    assert response.status_code == 200
    notifications = response.json()

    expected_notifications = [
        payload.expected_test_notification_1,
        payload.expected_test_notification_2,
    ]
    for notification, expected_notification in zip(
        notifications, expected_notifications
    ):
        expected_notification = {
            **expected_notification,
            "user_id": user_id,
            "time": time.isoformat(),
        }
        assert_real_matches_expected(notification, expected_notification)


@pytest.mark.asyncio
async def test_update_notification_status(
    fill_db_with_notifications, client: AsyncClient, test_session: AsyncSession
):
    notification = await NotificationRepo.get_by_fields(
        fields=[Notification.text],
        values=[payload.expected_test_notification_2["text"]],
        session=test_session,
    )
    assert notification is not None, "Notification not found"
    notification_id = notification.id
    response = await client.patch(
        f"/notifications/{notification_id}"
        f"?notification_status={NotificationStatusEnum.READ.value}"
    )
    assert response.status_code == 200
    updated_notification = response.json()
    assert_real_matches_expected(
        updated_notification, payload.expected_test_notification_2_update
    )
