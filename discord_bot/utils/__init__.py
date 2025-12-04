"""
Utility modules for the bot.
Re-exports from core/ for backward compatibility.
All business logic has been moved to core/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Re-export everything from core for backward compatibility
from core import (
    # Constants
    DAY_CODES, DAY_NAMES, TIMEZONES,
    # Timezone
    local_to_utc_time, utc_to_local_time,
    # Data
    load_data, save_data, get_user_data, save_user_data,
    load_courses, save_courses, get_course,
    # Cohort names
    COHORT_NAMES, CohortNameGenerator,
    # Google docs
    extract_doc_id, fetch_google_doc, parse_doc_tabs,
)

__all__ = [
    'DAY_CODES',
    'DAY_NAMES',
    'TIMEZONES',
    'local_to_utc_time',
    'utc_to_local_time',
    'load_data',
    'save_data',
    'get_user_data',
    'save_user_data',
    'load_courses',
    'save_courses',
    'get_course',
    'COHORT_NAMES',
    'CohortNameGenerator',
    'extract_doc_id',
    'fetch_google_doc',
    'parse_doc_tabs',
]
