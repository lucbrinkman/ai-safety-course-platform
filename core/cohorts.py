"""
Cohort creation and availability matching.
"""

from datetime import datetime
from typing import Optional
import pytz

from .data import get_user_data
from .timezone import utc_to_local_time


def find_availability_overlap(
    member_ids: list[str],
    get_user_data_fn=None
) -> Optional[tuple[str, int]]:
    """
    Find a 1-hour slot where all members are available.

    Args:
        member_ids: List of user ID strings
        get_user_data_fn: Function to fetch user data by ID (default: core.data.get_user_data)

    Returns:
        (day_name, hour) in UTC or None if no overlap found.
        Prefers fully available slots over if-needed slots.
    """
    if get_user_data_fn is None:
        get_user_data_fn = get_user_data

    # Collect all availability
    all_available = {}  # {(day, hour): [user_ids who are available]}
    all_if_needed = {}  # {(day, hour): [user_ids who marked if-needed]}

    for member_id in member_ids:
        user_data = get_user_data_fn(member_id)
        if not user_data:
            continue

        availability = user_data.get("availability", {})
        if_needed = user_data.get("if_needed", {})

        for day, slots in availability.items():
            for slot in slots:
                hour = int(slot.split(":")[0])
                key = (day, hour)
                if key not in all_available:
                    all_available[key] = []
                all_available[key].append(member_id)

        for day, slots in if_needed.items():
            for slot in slots:
                hour = int(slot.split(":")[0])
                key = (day, hour)
                if key not in all_if_needed:
                    all_if_needed[key] = []
                all_if_needed[key].append(member_id)

    member_id_set = set(member_ids)

    # First pass: look for slots where everyone is fully available
    for (day, hour), user_ids in all_available.items():
        if set(user_ids) == member_id_set:
            return (day, hour)

    # Second pass: look for slots where everyone is available or if-needed
    for (day, hour) in all_available.keys() | all_if_needed.keys():
        available_ids = set(all_available.get((day, hour), []))
        if_needed_ids = set(all_if_needed.get((day, hour), []))
        combined = available_ids | if_needed_ids

        if combined == member_id_set:
            return (day, hour)

    return None


def format_local_time(day: str, hour: int, tz_name: str) -> tuple[str, str]:
    """
    Convert UTC day/hour to local time string.

    Args:
        day: Day name in UTC (e.g., "Monday")
        hour: Hour in UTC (0-23)
        tz_name: Timezone string (e.g., "America/New_York")

    Returns:
        (local_day_name, formatted_time_string)
        e.g., ("Wednesday", "Wednesdays 3:00-4:00pm EST")
    """
    local_day, local_hour = utc_to_local_time(day, hour, tz_name)

    # Format hour as 12-hour time
    if local_hour == 0:
        start = "12:00am"
        end = "1:00am"
    elif local_hour < 12:
        start = f"{local_hour}:00am"
        end = f"{local_hour + 1}:00am" if local_hour + 1 < 12 else "12:00pm"
    elif local_hour == 12:
        start = "12:00pm"
        end = "1:00pm"
    else:
        start = f"{local_hour - 12}:00pm"
        end_hour = local_hour + 1
        if end_hour == 24:
            end = "12:00am"
        elif end_hour > 12:
            end = f"{end_hour - 12}:00pm"
        else:
            end = f"{end_hour}:00am"

    time_str = f"{start[:-2]}-{end}"

    # Get timezone abbreviation
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(pytz.UTC)
        abbrev = now.astimezone(tz).strftime('%Z')
    except:
        abbrev = tz_name

    return (local_day, f"{local_day}s {time_str} {abbrev}")


def get_timezone_abbrev(tz_name: str) -> str:
    """
    Get the current timezone abbreviation for a timezone.

    Args:
        tz_name: Timezone string (e.g., "America/New_York")

    Returns:
        Timezone abbreviation (e.g., "EST", "EDT")
    """
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(pytz.UTC)
        return now.astimezone(tz).strftime('%Z')
    except:
        return tz_name
