"""
Core business logic - platform-agnostic.
Can be used by Discord bot, web API, or any other interface.
"""

# Data persistence
from .data import (
    load_data, save_data, get_user_data, save_user_data,
    load_courses, save_courses, get_course
)

# Database (Supabase)
from .database import get_client, is_configured

# Constants
from .constants import DAY_CODES, DAY_NAMES, TIMEZONES

# Timezone utilities
from .timezone import local_to_utc_time, utc_to_local_time

# Google Docs integration
from .google_docs import extract_doc_id, fetch_google_doc, parse_doc_tabs, make_tab_url

# Cohort name generation
from .cohort_names import CohortNameGenerator, COHORT_NAMES

# Scheduling algorithm
from .scheduling import (
    Person, Group, DAY_MAP,
    parse_interval_string, calculate_total_available_time,
    is_group_valid, find_cohort_time_options, format_time_range,
    run_greedy_iteration, run_scheduling, balance_cohorts,
    convert_user_data_to_people
)

# Course management
from .courses import (
    get_all_courses, create_course, update_course, delete_course,
    add_course_week, update_course_week,
    mark_week_complete, get_user_progress, get_user_enrolled_courses, is_week_accessible
)

# Enrollment
from .enrollment import (
    get_user_profile, save_user_profile,
    get_enrolled_users, get_users_with_availability, get_facilitators, toggle_facilitator
)

# Cohorts / Availability
from .cohorts import (
    find_availability_overlap, format_local_time, get_timezone_abbrev
)

# Auth (Discord-to-Web flow)
from .auth import create_auth_code, get_or_create_user

# Stampy chatbot
from core import stampy

__all__ = [
    # Data
    'load_data', 'save_data', 'get_user_data', 'save_user_data',
    'load_courses', 'save_courses', 'get_course',
    # Database (Supabase)
    'get_client', 'is_configured',
    # Constants
    'DAY_CODES', 'DAY_NAMES', 'TIMEZONES',
    # Timezone
    'local_to_utc_time', 'utc_to_local_time',
    # Google Docs
    'extract_doc_id', 'fetch_google_doc', 'parse_doc_tabs', 'make_tab_url',
    # Cohort names
    'CohortNameGenerator', 'COHORT_NAMES',
    # Scheduling
    'Person', 'Group', 'DAY_MAP',
    'parse_interval_string', 'calculate_total_available_time',
    'is_group_valid', 'find_cohort_time_options', 'format_time_range',
    'run_greedy_iteration', 'run_scheduling', 'balance_cohorts',
    'convert_user_data_to_people',
    # Course management
    'get_all_courses', 'create_course', 'update_course', 'delete_course',
    'add_course_week', 'update_course_week',
    'mark_week_complete', 'get_user_progress', 'get_user_enrolled_courses', 'is_week_accessible',
    # Enrollment
    'get_user_profile', 'save_user_profile',
    'get_enrolled_users', 'get_users_with_availability', 'get_facilitators', 'toggle_facilitator',
    # Cohorts / Availability
    'find_availability_overlap', 'format_local_time', 'get_timezone_abbrev',
    # Auth
    'create_auth_code', 'get_or_create_user',
    # Stampy
    'stampy',
]
