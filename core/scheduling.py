"""
Cohort Scheduling - Platform Integration Layer

Wraps the cohort_scheduler package with platform-specific logic:
- Multi-course scheduling with cross-course conflict handling
- Database-backed cohort scheduling (schedule_cohort)
- User data conversion from stored formats
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, update

# Core scheduling algorithm from external package
import cohort_scheduler

from .constants import DAY_CODES
from .database import get_transaction
from .queries.cohorts import get_cohort_by_id
from .queries.groups import create_group, add_user_to_group
from .tables import courses_users, users


# Day code mapping (used by tests)
DAY_MAP = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4, 'S': 5, 'U': 6}


@dataclass
class Person:
    """
    Represents a person for scheduling.

    Extends the base cohort_scheduler Person with platform-specific fields
    (courses, experience) for multi-course scheduling support.
    """
    id: str
    name: str
    intervals: list  # List of (start_minutes, end_minutes)
    if_needed_intervals: list = field(default_factory=list)
    timezone: str = "UTC"
    courses: list = field(default_factory=list)
    experience: str = ""


@dataclass
class CourseSchedulingResult:
    """Result of scheduling a single course."""
    course_name: str
    groups: list  # list of Group
    score: int  # number of people scheduled
    unassigned: list  # list of Person


@dataclass
class MultiCourseSchedulingResult:
    """Result of scheduling across all courses."""
    course_results: dict  # course_name -> CourseSchedulingResult
    total_scheduled: int
    total_cohorts: int
    total_balance_moves: int
    total_people: int


@dataclass
class CohortSchedulingResult:
    """Result of scheduling a single cohort."""
    cohort_id: int
    cohort_name: str
    groups_created: int
    users_grouped: int
    users_ungroupable: int
    groups: list  # list of dicts with group_id, group_name, member_count, meeting_time


# Exceptions
class SchedulingError(Exception):
    """Base exception for scheduling errors."""
    pass


class NoUsersError(SchedulingError):
    """No users have availability set."""
    pass


class NoFacilitatorsError(SchedulingError):
    """Facilitator mode enabled but no facilitators marked."""
    pass


def calculate_total_available_time(person: Person) -> int:
    """Calculate total minutes of availability for a person."""
    total = 0
    for start, end in person.intervals:
        total += (end - start)
    for start, end in person.if_needed_intervals:
        total += (end - start)
    return total


def group_people_by_course(people: list) -> dict:
    """
    Group people by course.

    People enrolled in multiple courses appear in multiple groups.
    People with no courses go into "Uncategorized".

    Returns: dict mapping course_name -> list of Person
    """
    people_by_course = {}
    for person in people:
        if person.courses:
            for course in person.courses:
                if course not in people_by_course:
                    people_by_course[course] = []
                people_by_course[course].append(person)
        else:
            if "Uncategorized" not in people_by_course:
                people_by_course["Uncategorized"] = []
            people_by_course["Uncategorized"].append(person)
    return people_by_course


def remove_blocked_intervals(person: Person, blocked_times: list) -> Person:
    """
    Return new Person with intervals that conflict with blocked_times removed.

    Args:
        person: The person to adjust
        blocked_times: List of (start, end) tuples representing already-assigned times

    Returns:
        New Person with conflicting intervals removed
    """
    if not blocked_times:
        return person

    new_intervals = []
    for start, end in person.intervals:
        conflicts = False
        for b_start, b_end in blocked_times:
            if start < b_end and end > b_start:
                conflicts = True
                break
        if not conflicts:
            new_intervals.append((start, end))

    new_if_needed = []
    for start, end in person.if_needed_intervals:
        conflicts = False
        for b_start, b_end in blocked_times:
            if start < b_end and end > b_start:
                conflicts = True
                break
        if not conflicts:
            new_if_needed.append((start, end))

    return Person(
        id=person.id,
        name=person.name,
        intervals=new_intervals,
        if_needed_intervals=new_if_needed,
        timezone=person.timezone,
        courses=person.courses,
        experience=person.experience
    )


async def run_scheduling(people: list, meeting_length: int = 60, min_people: int = 4,
                         max_people: int = 8, num_iterations: int = 1000,
                         time_increment: int = 30, randomness: float = 0.5,
                         facilitator_ids: set = None, facilitator_max_cohorts: dict = None,
                         use_if_needed: bool = True, progress_callback=None) -> tuple:
    """
    Run the full stochastic greedy scheduling algorithm.

    Returns (best_solution, best_score, best_iteration, total_iterations)
    for backward compatibility.
    """
    result = cohort_scheduler.schedule(
        people=people,
        meeting_length=meeting_length,
        min_people=min_people,
        max_people=max_people,
        num_iterations=num_iterations,
        time_increment=time_increment,
        randomness=randomness,
        facilitator_ids=facilitator_ids,
        facilitator_max_cohorts=facilitator_max_cohorts,
        use_if_needed=use_if_needed,
        balance=False,  # We handle balancing separately in schedule_people
        progress_callback=progress_callback,
    )

    return result.groups, result.score, result.best_iteration, result.iterations_run


async def schedule_people(
    all_people: list,
    meeting_length: int = 60,
    min_people: int = 4,
    max_people: int = 8,
    num_iterations: int = 1000,
    balance: bool = True,
    use_if_needed: bool = True,
    facilitator_ids: set = None,
    progress_callback=None
) -> MultiCourseSchedulingResult:
    """
    Run scheduling across multiple courses, handling cross-course conflicts.

    People enrolled in multiple courses are scheduled for each course,
    with later courses seeing reduced availability (blocked by earlier assignments).

    Args:
        all_people: List of Person objects to schedule
        meeting_length: Meeting duration in minutes
        min_people: Minimum people per cohort
        max_people: Maximum people per cohort
        num_iterations: Scheduling algorithm iterations per course
        balance: Whether to balance cohort sizes after scheduling
        use_if_needed: Include "if needed" availability slots
        facilitator_ids: Set of person IDs who are facilitators (or None)
        progress_callback: Optional async fn(course_name, iteration, total, best_score, people_count)

    Returns:
        MultiCourseSchedulingResult with all course results and totals
    """
    # Group people by course
    people_by_course = group_people_by_course(all_people)

    # Track results
    course_results = {}
    total_scheduled = 0
    total_cohorts = 0
    total_balance_moves = 0

    # Track assigned times for each person across courses (for conflict prevention)
    # person_id -> list of (start, end) tuples
    assigned_times = {}

    for course_name, people in people_by_course.items():
        if len(people) < min_people:
            # Not enough people for this course
            course_results[course_name] = CourseSchedulingResult(
                course_name=course_name,
                groups=[],
                score=0,
                unassigned=people
            )
            continue

        # Get facilitators for this course
        course_facilitator_ids = None
        if facilitator_ids:
            course_facilitator_ids = {p.id for p in people if p.id in facilitator_ids}
            if not course_facilitator_ids:
                # No facilitators in this course, skip if facilitator mode
                course_results[course_name] = CourseSchedulingResult(
                    course_name=course_name,
                    groups=[],
                    score=0,
                    unassigned=people
                )
                continue

        # Remove already-assigned times from people's availability
        adjusted_people = [
            remove_blocked_intervals(person, assigned_times.get(person.id, []))
            for person in people
        ]

        # Create course-specific progress callback
        async def course_progress(iteration, total, best_score, people_count):
            if progress_callback:
                await progress_callback(course_name, iteration, total, best_score, people_count)

        # Run scheduling for this course
        solution, score, best_iter, total_iter = await run_scheduling(
            people=adjusted_people,
            meeting_length=meeting_length,
            min_people=min_people,
            max_people=max_people,
            num_iterations=num_iterations,
            facilitator_ids=course_facilitator_ids,
            use_if_needed=use_if_needed,
            progress_callback=course_progress
        )

        # Balance cohorts if enabled
        moves = 0
        if balance and solution and len(solution) >= 2:
            moves = cohort_scheduler.balance_groups(solution, meeting_length, use_if_needed=use_if_needed)
            total_balance_moves += moves

        # Track assigned times for multi-course users
        if solution:
            for group in solution:
                if group.selected_time:
                    for person in group.people:
                        if person.id not in assigned_times:
                            assigned_times[person.id] = []
                        assigned_times[person.id].append(group.selected_time)

        # Compute unassigned
        if solution:
            assigned_ids = {p.id for g in solution for p in g.people}
            unassigned = [p for p in people if p.id not in assigned_ids]
            total_scheduled += score
            total_cohorts += len(solution)
        else:
            unassigned = people
            solution = []

        course_results[course_name] = CourseSchedulingResult(
            course_name=course_name,
            groups=solution,
            score=score,
            unassigned=unassigned
        )

    return MultiCourseSchedulingResult(
        course_results=course_results,
        total_scheduled=total_scheduled,
        total_cohorts=total_cohorts,
        total_balance_moves=total_balance_moves,
        total_people=len(all_people)
    )


async def schedule_cohort(
    cohort_id: int,
    meeting_length: int = 60,
    min_people: int = 4,
    max_people: int = 8,
    num_iterations: int = 1000,
    balance: bool = True,
    use_if_needed: bool = True,
    progress_callback=None,
) -> CohortSchedulingResult:
    """
    Run scheduling for a specific cohort and persist results to database.

    1. Load users from courses_users WHERE cohort_id=X AND grouping_status='awaiting_grouping'
    2. Get their availability from users table
    3. Run scheduling algorithm
    4. Insert groups into 'groups' table
    5. Insert memberships into 'groups_users' table
    6. Update courses_users.grouping_status to 'grouped' or 'ungroupable'

    Returns: CohortSchedulingResult with summary
    """
    async with get_transaction() as conn:
        # Get cohort info
        cohort = await get_cohort_by_id(conn, cohort_id)
        if not cohort:
            raise ValueError(f"Cohort {cohort_id} not found")

        # Load users awaiting grouping for this cohort
        query = (
            select(
                users.c.user_id,
                users.c.discord_id,
                users.c.nickname,
                users.c.discord_username,
                users.c.timezone,
                users.c.availability_utc,
                users.c.if_needed_availability_utc,
                courses_users.c.cohort_role,
            )
            .join(courses_users, users.c.user_id == courses_users.c.user_id)
            .where(courses_users.c.cohort_id == cohort_id)
            .where(courses_users.c.grouping_status == "awaiting_grouping")
        )
        result = await conn.execute(query)
        user_rows = [dict(row) for row in result.mappings()]

        if not user_rows:
            return CohortSchedulingResult(
                cohort_id=cohort_id,
                cohort_name=cohort["cohort_name"],
                groups_created=0,
                users_grouped=0,
                users_ungroupable=0,
                groups=[],
            )

        # Convert to Person objects for scheduling
        people = []
        user_id_map = {}  # discord_id -> user_id for later
        facilitator_ids = set()

        for row in user_rows:
            discord_id = row["discord_id"]
            user_id_map[discord_id] = row["user_id"]

            # Parse availability
            intervals = cohort_scheduler.parse_interval_string(row["availability_utc"] or "")
            if_needed = cohort_scheduler.parse_interval_string(row["if_needed_availability_utc"] or "")

            if not intervals and not if_needed:
                continue  # Skip users with no availability

            name = row["nickname"] or row["discord_username"] or f"User {row['user_id']}"
            person = Person(
                id=discord_id,
                name=name,
                intervals=intervals,
                if_needed_intervals=if_needed,
                timezone=row["timezone"] or "UTC",
            )
            people.append(person)

            if row["cohort_role"] == "facilitator":
                facilitator_ids.add(discord_id)

        if not people:
            return CohortSchedulingResult(
                cohort_id=cohort_id,
                cohort_name=cohort["cohort_name"],
                groups_created=0,
                users_grouped=0,
                users_ungroupable=len(user_rows),
                groups=[],
            )

        # Run scheduling algorithm
        facilitator_ids_param = facilitator_ids if facilitator_ids else None
        solution, score, best_iter, total_iter = await run_scheduling(
            people=people,
            meeting_length=meeting_length,
            min_people=min_people,
            max_people=max_people,
            num_iterations=num_iterations,
            facilitator_ids=facilitator_ids_param,
            use_if_needed=use_if_needed,
            progress_callback=progress_callback,
        )

        # Balance if requested
        if balance and solution and len(solution) >= 2:
            cohort_scheduler.balance_groups(solution, meeting_length, use_if_needed=use_if_needed)

        # Persist groups to database
        created_groups = []
        grouped_user_ids = set()

        if solution:
            for i, group in enumerate(solution, 1):
                # Format meeting time
                if group.selected_time:
                    meeting_time = cohort_scheduler.format_time_range(*group.selected_time)
                else:
                    meeting_time = "TBD"

                # Create group record
                group_record = await create_group(
                    conn,
                    cohort_id=cohort_id,
                    group_name=f"Group {i}",
                    recurring_meeting_time_utc=meeting_time,
                )

                # Add members to group
                for person in group.people:
                    user_id = user_id_map.get(person.id)
                    if user_id:
                        role = "facilitator" if person.id in facilitator_ids else "participant"
                        await add_user_to_group(conn, group_record["group_id"], user_id, role)
                        grouped_user_ids.add(user_id)

                created_groups.append({
                    "group_id": group_record["group_id"],
                    "group_name": group_record["group_name"],
                    "member_count": len(group.people),
                    "meeting_time": meeting_time,
                })

        # Update grouping_status for all users
        all_user_ids = [row["user_id"] for row in user_rows]
        ungroupable_user_ids = [uid for uid in all_user_ids if uid not in grouped_user_ids]

        if grouped_user_ids:
            await conn.execute(
                update(courses_users)
                .where(courses_users.c.cohort_id == cohort_id)
                .where(courses_users.c.user_id.in_(list(grouped_user_ids)))
                .values(grouping_status="grouped")
            )

        if ungroupable_user_ids:
            await conn.execute(
                update(courses_users)
                .where(courses_users.c.cohort_id == cohort_id)
                .where(courses_users.c.user_id.in_(ungroupable_user_ids))
                .values(grouping_status="ungroupable")
            )

        return CohortSchedulingResult(
            cohort_id=cohort_id,
            cohort_name=cohort["cohort_name"],
            groups_created=len(created_groups),
            users_grouped=len(grouped_user_ids),
            users_ungroupable=len(ungroupable_user_ids),
            groups=created_groups,
        )


async def schedule(
    meeting_length: int = 60,
    min_people: int = 4,
    max_people: int = 8,
    num_iterations: int = 1000,
    balance: bool = True,
    use_if_needed: bool = True,
    facilitator_mode: bool = False,
    progress_callback=None
) -> MultiCourseSchedulingResult:
    """
    Load users from database and run scheduling across all courses.

    This is the main entry point for scheduling - handles data loading,
    facilitator extraction, and runs the scheduling algorithm.

    Args:
        meeting_length: Meeting duration in minutes
        min_people: Minimum people per cohort
        max_people: Maximum people per cohort
        num_iterations: Scheduling algorithm iterations per course
        balance: Whether to balance cohort sizes after scheduling
        use_if_needed: Include "if needed" availability slots
        facilitator_mode: Require each cohort to have one facilitator
        progress_callback: Optional async fn(course_name, iteration, total, best_score, people_count)

    Returns:
        MultiCourseSchedulingResult with all course results and totals

    Raises:
        NoUsersError: If no users have availability set
        NoFacilitatorsError: If facilitator_mode=True but no facilitators marked
    """
    # Local import to avoid circular dependency (enrollment imports from scheduling)
    from .enrollment import get_people_for_scheduling

    # Load from database
    all_people, user_data = await get_people_for_scheduling()

    if not all_people:
        raise NoUsersError("No users have set their availability yet")

    # Extract facilitators if needed
    facilitator_ids = None
    if facilitator_mode:
        facilitator_ids = {
            user_id for user_id, data in user_data.items()
            if data.get("is_facilitator", False)
        }
        if not facilitator_ids:
            raise NoFacilitatorsError("No facilitators are marked")

    # Run scheduling
    return await schedule_people(
        all_people=all_people,
        meeting_length=meeting_length,
        min_people=min_people,
        max_people=max_people,
        num_iterations=num_iterations,
        balance=balance,
        use_if_needed=use_if_needed,
        facilitator_ids=facilitator_ids,
        progress_callback=progress_callback
    )
