"""
User enrollment and profile management.
"""

from .data import load_data, get_user_data, save_user_data


def get_user_profile(user_id: str) -> dict:
    """
    Get a user's full profile.

    Returns:
        User profile dict or empty dict if not found
    """
    return get_user_data(user_id)


def save_user_profile(
    user_id: str,
    name: str = None,
    courses: list = None,
    experience: str = None,
    timezone: str = None,
    availability: dict = None,
    if_needed: dict = None,
    is_facilitator: bool = None
) -> dict:
    """
    Save or update a user's profile.

    Args:
        user_id: User ID
        name: Display name
        courses: List of course IDs
        experience: Experience level (beginner/intermediate/advanced)
        timezone: Timezone string (e.g., "America/New_York")
        availability: Dict of day -> list of time slots (in UTC)
        if_needed: Dict of day -> list of if-needed time slots (in UTC)
        is_facilitator: Whether user is a facilitator

    Returns:
        Updated user profile
    """
    user_data = get_user_data(user_id)

    if name is not None:
        user_data["name"] = name
    if courses is not None:
        user_data["courses"] = courses
    if experience is not None:
        user_data["experience"] = experience
    if timezone is not None:
        user_data["timezone"] = timezone
    if availability is not None:
        user_data["availability"] = availability
    if if_needed is not None:
        user_data["if_needed"] = if_needed
    if is_facilitator is not None:
        user_data["is_facilitator"] = is_facilitator

    save_user_data(user_id, user_data)
    return user_data


def get_enrolled_users(course_id: str = None) -> dict:
    """
    Get all enrolled users, optionally filtered by course.

    Args:
        course_id: If provided, only return users in this course

    Returns:
        Dict of user_id -> user_data
    """
    all_users = load_data()

    if course_id is None:
        return all_users

    return {
        user_id: data
        for user_id, data in all_users.items()
        if course_id in data.get("courses", [])
    }


def get_users_with_availability() -> dict:
    """
    Get all users who have set availability.

    Returns:
        Dict of user_id -> user_data for users with availability
    """
    all_users = load_data()

    return {
        user_id: data
        for user_id, data in all_users.items()
        if data.get("availability") or data.get("if_needed")
    }


def get_facilitators() -> dict:
    """
    Get all users marked as facilitators.

    Returns:
        Dict of user_id -> user_data for facilitators
    """
    all_users = load_data()

    return {
        user_id: data
        for user_id, data in all_users.items()
        if data.get("is_facilitator", False)
    }


def toggle_facilitator(user_id: str) -> bool:
    """
    Toggle a user's facilitator status.

    Returns:
        New facilitator status (True/False)
    """
    user_data = get_user_data(user_id)

    if not user_data:
        return False

    current_status = user_data.get("is_facilitator", False)
    user_data["is_facilitator"] = not current_status
    save_user_data(user_id, user_data)

    return not current_status
