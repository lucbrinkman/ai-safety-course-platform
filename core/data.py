"""
Data storage utilities for user and course data persistence.
"""

import json
import os
from pathlib import Path

# Data directory - can be overridden via DATA_DIR environment variable
# Default: discord_bot/ directory (for backwards compatibility)
_PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(os.environ.get('DATA_DIR', _PROJECT_ROOT / 'discord_bot'))

DATA_FILE = DATA_DIR / "user_data.json"
COURSES_FILE = DATA_DIR / "courses.json"


def load_data() -> dict:
    """Load all user data from the JSON file."""
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load data from {DATA_FILE}: {e}")
        return {}


def save_data(data: dict) -> None:
    """Save all user data to the JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Failed to save data to {DATA_FILE}: {e}")
        raise


def get_user_data(user_id: str) -> dict:
    """Get data for a specific user."""
    data = load_data()
    return data.get(user_id, {})


def save_user_data(user_id: str, user_data: dict) -> None:
    """Save data for a specific user."""
    data = load_data()
    data[user_id] = user_data
    save_data(data)


# ============ COURSE DATA ============

def load_courses() -> dict:
    """Load all course data from the JSON file."""
    if not COURSES_FILE.exists():
        return {}
    try:
        with open(COURSES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load courses from {COURSES_FILE}: {e}")
        return {}


def save_courses(data: dict) -> None:
    """Save all course data to the JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(COURSES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Failed to save courses to {COURSES_FILE}: {e}")
        raise


def get_course(course_id: str) -> dict | None:
    """Get data for a specific course."""
    courses = load_courses()
    return courses.get(course_id)
