"""
Course management business logic.
"""

from .data import load_courses, save_courses, get_course, get_user_data, save_user_data


def get_all_courses() -> dict:
    """Get all courses."""
    return load_courses()


def create_course(course_id: str, name: str, doc_url: str, category_id: int = None, weeks: list = None) -> dict:
    """
    Create a new course.

    Args:
        course_id: Unique identifier for the course
        name: Display name
        doc_url: Google Doc URL
        category_id: Discord category ID (optional, set by cog)
        weeks: List of week data (optional)

    Returns:
        The created course data
    """
    courses = load_courses()

    course_data = {
        "name": name,
        "doc_url": doc_url,
        "category_id": category_id,
        "weeks": weeks or []
    }

    courses[course_id] = course_data
    save_courses(courses)

    return course_data


def update_course(course_id: str, **kwargs) -> dict | None:
    """
    Update a course's fields.

    Args:
        course_id: Course to update
        **kwargs: Fields to update (name, doc_url, category_id, weeks)

    Returns:
        Updated course data or None if not found
    """
    courses = load_courses()

    if course_id not in courses:
        return None

    for key, value in kwargs.items():
        if value is not None:
            courses[course_id][key] = value

    save_courses(courses)
    return courses[course_id]


def delete_course(course_id: str) -> bool:
    """
    Delete a course.

    Returns:
        True if deleted, False if not found
    """
    courses = load_courses()

    if course_id not in courses:
        return False

    del courses[course_id]
    save_courses(courses)
    return True


def add_course_week(course_id: str, week_data: dict) -> dict | None:
    """
    Add a week to a course.

    Args:
        course_id: Course to add week to
        week_data: Dict with number, title, tab_id, tab_url, channel_id, message_id

    Returns:
        Updated course data or None if course not found
    """
    courses = load_courses()

    if course_id not in courses:
        return None

    courses[course_id]["weeks"].append(week_data)
    save_courses(courses)
    return courses[course_id]


def update_course_week(course_id: str, week_number: int, **kwargs) -> dict | None:
    """
    Update a specific week in a course.

    Args:
        course_id: Course containing the week
        week_number: Week number (1-indexed)
        **kwargs: Fields to update

    Returns:
        Updated course data or None if not found
    """
    courses = load_courses()

    if course_id not in courses:
        return None

    for week in courses[course_id]["weeks"]:
        if week["number"] == week_number:
            for key, value in kwargs.items():
                if value is not None:
                    week[key] = value
            break

    save_courses(courses)
    return courses[course_id]


# ============ Progress Tracking ============

def mark_week_complete(user_id: str, course_id: str, week_num: int) -> dict:
    """
    Mark a week as completed for a user.

    Returns:
        Updated user progress data for this course
    """
    user_data = get_user_data(user_id)

    if not user_data:
        user_data = {}

    progress = user_data.setdefault("course_progress", {}).setdefault(
        course_id, {"current_week": 1, "completed_weeks": []}
    )

    if week_num not in progress["completed_weeks"]:
        progress["completed_weeks"].append(week_num)
        progress["current_week"] = max(progress["current_week"], week_num + 1)

    save_user_data(user_id, user_data)
    return progress


def get_user_progress(user_id: str, course_id: str) -> dict:
    """
    Get a user's progress in a course.

    Returns:
        Progress dict with current_week and completed_weeks
    """
    user_data = get_user_data(user_id)

    if not user_data:
        return {"current_week": 1, "completed_weeks": []}

    return user_data.get("course_progress", {}).get(
        course_id, {"current_week": 1, "completed_weeks": []}
    )


def get_user_enrolled_courses(user_id: str) -> list:
    """Get list of course IDs a user is enrolled in."""
    user_data = get_user_data(user_id)
    return user_data.get("courses", []) if user_data else []


def is_week_accessible(user_id: str, course_id: str, week_num: int) -> bool:
    """Check if a user can access a specific week."""
    progress = get_user_progress(user_id, course_id)
    return week_num <= progress["current_week"] or week_num in progress["completed_weeks"]
