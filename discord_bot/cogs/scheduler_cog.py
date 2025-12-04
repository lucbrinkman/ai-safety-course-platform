"""
Scheduler Cog - Discord adapter for the scheduling algorithm.
"""

import discord
from discord import app_commands
from discord.ext import commands

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import (
    load_data, DAY_CODES,
    Person, run_scheduling, balance_cohorts, find_cohort_time_options,
    format_time_range, calculate_total_available_time,
    convert_user_data_to_people
)


class SchedulerCog(commands.Cog):
    """Cog for cohort scheduling functionality."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="schedule", description="Run the cohort scheduling algorithm")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        meeting_length="Meeting length in minutes (default: 60)",
        min_people="Minimum people per cohort (default: 4)",
        max_people="Maximum people per cohort (default: 8)",
        iterations="Number of iterations to run (default: 1000)",
        balance="Balance cohort sizes after scheduling (default: True)",
        use_if_needed="Include 'if needed' times in scheduling (default: True)",
        facilitator_mode="Require each cohort to have one facilitator (default: False)"
    )
    async def schedule(self, interaction: discord.Interaction,
                       meeting_length: int = 60,
                       min_people: int = 4,
                       max_people: int = 8,
                       iterations: int = 1000,
                       balance: bool = True,
                       use_if_needed: bool = True,
                       facilitator_mode: bool = False):
        """Run the scheduling algorithm on all registered users."""

        await interaction.response.defer()

        # Load and convert user data
        user_data = load_data()
        all_people = convert_user_data_to_people(user_data, DAY_CODES)

        if not all_people:
            await interaction.followup.send(
                "No users have set their availability yet!",
                ephemeral=True
            )
            return

        # Collect facilitator IDs if facilitator mode is enabled
        facilitator_ids = None
        if facilitator_mode:
            facilitator_ids = {
                user_id for user_id, data in user_data.items()
                if data.get("is_facilitator", False)
            }
            if not facilitator_ids:
                await interaction.followup.send(
                    "Facilitator mode is enabled but no facilitators are marked!\n"
                    "Use `/toggle-facilitator` to mark people as facilitators.",
                    ephemeral=True
                )
                return

        # Group people by course (people can appear in multiple courses)
        people_by_course = {}
        for person in all_people:
            if person.courses:
                for course in person.courses:
                    if course not in people_by_course:
                        people_by_course[course] = []
                    people_by_course[course].append(person)
            else:
                # Handle uncategorized
                if "Uncategorized" not in people_by_course:
                    people_by_course["Uncategorized"] = []
                people_by_course["Uncategorized"].append(person)

        # Progress message
        progress_msg = await interaction.followup.send(
            f"🔄 Running scheduling algorithm...\n"
            f"Courses: {len(people_by_course)} | Total people: {len(all_people)}",
            ephemeral=False
        )

        # Run scheduling for each course
        all_solutions = {}  # course -> (solution, score, unassigned)
        total_scheduled = 0
        total_cohorts = 0
        total_moves = 0

        # Track assigned times for each person across courses
        # person_id -> list of (start, end) tuples
        assigned_times = {}

        for course_name, people in people_by_course.items():
            if len(people) < min_people:
                # Not enough people for this course
                all_solutions[course_name] = ([], 0, people)
                continue

            # Get facilitators for this course
            course_facilitator_ids = None
            if facilitator_ids:
                course_facilitator_ids = {p.id for p in people if p.id in facilitator_ids}
                if not course_facilitator_ids:
                    # No facilitators in this course, skip if facilitator mode
                    all_solutions[course_name] = ([], 0, people)
                    continue

            # Remove already-assigned times from people's availability
            adjusted_people = []
            for person in people:
                if person.id in assigned_times:
                    # Create new person with blocked times removed
                    blocked = assigned_times[person.id]
                    new_intervals = []
                    for start, end in person.intervals:
                        # Check if this interval conflicts with any blocked time
                        conflicts = False
                        for b_start, b_end in blocked:
                            if start < b_end and end > b_start:
                                conflicts = True
                                break
                        if not conflicts:
                            new_intervals.append((start, end))

                    new_if_needed = []
                    for start, end in person.if_needed_intervals:
                        conflicts = False
                        for b_start, b_end in blocked:
                            if start < b_end and end > b_start:
                                conflicts = True
                                break
                        if not conflicts:
                            new_if_needed.append((start, end))

                    adjusted_person = Person(
                        id=person.id,
                        name=person.name,
                        intervals=new_intervals,
                        if_needed_intervals=new_if_needed,
                        timezone=person.timezone,
                        courses=person.courses,
                        experience=person.experience
                    )
                    adjusted_people.append(adjusted_person)
                else:
                    adjusted_people.append(person)

            async def update_progress(current, total, best_score, total_people):
                try:
                    await progress_msg.edit(
                        content=f"🔄 Scheduling **{course_name}**...\n"
                                f"Iteration: {current}/{total} | "
                                f"Best: {best_score}/{total_people}"
                    )
                except:
                    pass

            # Run scheduling for this course
            solution, score, best_iter, total_iter = await run_scheduling(
                people=adjusted_people,
                meeting_length=meeting_length,
                min_people=min_people,
                max_people=max_people,
                num_iterations=iterations,
                facilitator_ids=course_facilitator_ids,
                use_if_needed=use_if_needed,
                progress_callback=update_progress
            )

            # Balance cohorts if enabled
            if balance and solution and len(solution) >= 2:
                moves = balance_cohorts(solution, meeting_length, use_if_needed=use_if_needed)
                total_moves += moves

            # Track assigned times for multi-course users
            if solution:
                for group in solution:
                    if group.selected_time:
                        for person in group.people:
                            if person.id not in assigned_times:
                                assigned_times[person.id] = []
                            assigned_times[person.id].append(group.selected_time)

            # Track unassigned
            if solution:
                assigned_ids = {p.id for g in solution for p in g.people}
                unassigned = [p for p in people if p.id not in assigned_ids]
                total_scheduled += score
                total_cohorts += len(solution)
            else:
                unassigned = people
                solution = []

            all_solutions[course_name] = (solution, score, unassigned)

        # Build results embed
        placement_rate = total_scheduled * 100 // len(all_people) if all_people else 0

        embed = discord.Embed(
            title="📅 Scheduling Complete!",
            color=discord.Color.green() if placement_rate >= 80 else discord.Color.yellow()
        )

        balance_info = f"\n**Balance moves:** {total_moves}" if total_moves > 0 else ""
        embed.add_field(
            name="Summary",
            value=f"**Courses:** {len(people_by_course)}\n"
                  f"**Total cohorts:** {total_cohorts}\n"
                  f"**People scheduled:** {total_scheduled}/{len(all_people)} ({placement_rate}%){balance_info}",
            inline=False
        )

        # List cohorts by course
        cohort_num = 1
        for course_name, (solution, score, unassigned) in all_solutions.items():
            if solution:
                embed.add_field(
                    name=f"📚 {course_name}",
                    value=f"{len(solution)} cohort(s), {score} people",
                    inline=False
                )

                for group in solution:
                    members = [p.name for p in group.people]
                    time_str = format_time_range(*group.selected_time) if group.selected_time else "No common time"

                    embed.add_field(
                        name=f"Cohort {cohort_num} ({len(group.people)} people)",
                        value=f"**Time (UTC):** {time_str}\n"
                              f"**Members:** {', '.join(members)}",
                        inline=False
                    )
                    cohort_num += 1

            # Show unassigned for this course
            if unassigned:
                unassigned_names = [p.name for p in unassigned]
                embed.add_field(
                    name=f"⚠️ {course_name} - Unassigned ({len(unassigned)})",
                    value=", ".join(unassigned_names[:10]) + ("..." if len(unassigned_names) > 10 else ""),
                    inline=False
                )

        await progress_msg.edit(content=None, embed=embed)

    @app_commands.command(name="list-users", description="List all users with availability")
    async def list_users(self, interaction: discord.Interaction):
        """List all users who have set their availability."""

        user_data = load_data()
        people = convert_user_data_to_people(user_data, DAY_CODES)

        if not people:
            await interaction.response.send_message(
                "No users have set their availability yet. Use `/signup` to register!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📋 Registered Users ({len(people)})",
            color=discord.Color.blue()
        )

        for person in people[:25]:  # Show max 25
            total_time = calculate_total_available_time(person)
            hours = total_time // 60

            # Check facilitator status
            is_facilitator = user_data.get(person.id, {}).get("is_facilitator", False)
            facilitator_badge = " ⭐" if is_facilitator else ""

            courses_str = ", ".join(person.courses) if person.courses else "N/A"
            embed.add_field(
                name=f"{person.name}{facilitator_badge}",
                value=f"Available: {hours}h/week\n"
                      f"Courses: {courses_str}",
                inline=True
            )

        if len(people) > 25:
            embed.set_footer(text=f"... and {len(people) - 25} more")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
