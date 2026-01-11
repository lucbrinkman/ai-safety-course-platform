"""
Notification system for sending emails and Discord messages.

Public API:
    send_notification(user_id, message_type, context) - Send immediately
    schedule_reminder(job_id, run_at, ...) - Schedule for later
    cancel_reminders(pattern) - Cancel scheduled jobs
"""

from .dispatcher import send_notification
from .scheduler import schedule_reminder, cancel_reminders, init_scheduler, shutdown_scheduler

__all__ = [
    "send_notification",
    "schedule_reminder",
    "cancel_reminders",
    "init_scheduler",
    "shutdown_scheduler",
]
