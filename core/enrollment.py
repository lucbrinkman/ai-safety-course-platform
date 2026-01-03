"""
Enrollment and scheduling helpers.

Converts user data to Person objects for scheduling algorithm.
User profile functions are in core/users.py.
"""

import json

import cohort_scheduler

from .database import get_connection
from .queries import users as user_queries
from .scheduling import Person
from .constants import DAY_CODES


async def get_people_for_scheduling() -> tuple[list[Person], dict[str, dict]]:
    """
    Get all users with availability as Person objects for scheduling.

    Also returns the raw user data dict for facilitator checking.

    Returns:
        Tuple of (list of Person objects, dict of discord_id -> user data)
    """
    async with get_connection() as conn:
        users = await user_queries.get_all_users_with_availability(conn)
        facilitator_list = await user_queries.get_facilitators(conn)

    # Create set of facilitator discord_ids for quick lookup
    facilitator_discord_ids = {f["discord_id"] for f in facilitator_list}

    people = []
    user_data_dict = {}

    for user in users:
        discord_id = user.get("discord_id")
        if not discord_id:
            continue

        # Parse availability from JSON strings
        availability_str = user.get("availability_utc")
        if_needed_str = user.get("if_needed_availability_utc")

        availability = json.loads(availability_str) if availability_str else {}
        if_needed = json.loads(if_needed_str) if if_needed_str else {}

        if not availability and not if_needed:
            continue

        # Convert availability dict to interval strings, then parse to tuples
        interval_strs = []
        for day, slots in availability.items():
            day_code = DAY_CODES.get(day, day[0])
            for slot in sorted(slots):
                hour = int(slot.split(":")[0])
                end_hour = hour + 1
                interval_str = f"{day_code}{slot} {day_code}{end_hour:02d}:00"
                interval_strs.append(interval_str)

        # Parse interval strings to (start_minutes, end_minutes) tuples
        intervals = cohort_scheduler.parse_interval_string(", ".join(interval_strs)) if interval_strs else []

        # Convert if_needed dict to interval strings, then parse to tuples
        if_needed_strs = []
        for day, slots in if_needed.items():
            day_code = DAY_CODES.get(day, day[0])
            for slot in sorted(slots):
                hour = int(slot.split(":")[0])
                end_hour = hour + 1
                interval_str = f"{day_code}{slot} {day_code}{end_hour:02d}:00"
                if_needed_strs.append(interval_str)

        if_needed_intervals = cohort_scheduler.parse_interval_string(", ".join(if_needed_strs)) if if_needed_strs else []

        # Get name
        name = user.get("nickname") or user.get("discord_username") or f"User_{discord_id[:8]}"

        # Create Person object
        person = Person(
            id=discord_id,
            name=name,
            intervals=intervals,
            if_needed_intervals=if_needed_intervals,
            timezone=user.get("timezone", "UTC"),
            courses=[],  # Course enrollment handled separately
            experience=None
        )
        people.append(person)

        # Store user data for facilitator checking
        user_data_dict[discord_id] = {
            "name": name,
            "timezone": user.get("timezone", "UTC"),
            "is_facilitator": discord_id in facilitator_discord_ids,
        }

    return people, user_data_dict
