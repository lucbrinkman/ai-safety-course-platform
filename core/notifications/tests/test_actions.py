"""Tests for high-level notification actions."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from zoneinfo import ZoneInfo


class TestNotifyGroupAssigned:
    @pytest.mark.asyncio
    async def test_sends_notification_with_calendar(self):
        from core.notifications.actions import notify_group_assigned

        mock_send = AsyncMock(return_value={"email": True, "discord": True})
        mock_schedule = MagicMock()
        mock_user = {
            "user_id": 1,
            "email": "alice@example.com",
            "discord_id": "123456",
            "nickname": "Alice",
        }

        with patch("core.notifications.dispatcher.get_user_by_id", AsyncMock(return_value=mock_user)):
            with patch("core.notifications.actions.send_notification", mock_send):
                with patch("core.notifications.actions.schedule_reminder", mock_schedule):
                    with patch("core.notifications.actions.create_calendar_invite", return_value="ICS_DATA"):
                        await notify_group_assigned(
                            user_id=1,
                            group_name="Curious Capybaras",
                            meeting_time_utc="Wednesday 15:00",
                            member_names=["Alice", "Bob"],
                            discord_channel_id="123456",
                            meeting_id=42,
                        )

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["message_type"] == "group_assigned"
        assert "calendar_ics" in call_kwargs


class TestScheduleMeetingReminders:
    def test_schedules_24h_and_1h_reminders(self):
        from core.notifications.actions import schedule_meeting_reminders

        mock_schedule = MagicMock()
        meeting_time = datetime.now(ZoneInfo("UTC")) + timedelta(days=2)

        with patch("core.notifications.actions.schedule_reminder", mock_schedule):
            schedule_meeting_reminders(
                meeting_id=42,
                meeting_time=meeting_time,
                user_ids=[1, 2, 3],
                group_name="Test Group",
                discord_channel_id="123456",
            )

        # Should schedule 4 jobs: 24h, 1h, 3d lesson nudge, 1d lesson nudge
        assert mock_schedule.call_count == 4
