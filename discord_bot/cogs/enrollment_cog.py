"""
Enrollment Cog - Discord adapter for user signup and profile management.

The /signup command now generates a web link with an auth code,
redirecting users to the web frontend for profile setup.
"""

import json
import os
import discord
from discord import app_commands
from discord.ext import commands

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import (
    DAY_CODES,
    utc_to_local_time,
    get_user_profile,
    toggle_facilitator,
    create_auth_code,
)


class EnrollmentCog(commands.Cog):
    """Cog for user enrollment and profile management."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="signup", description="Sign up for the AI Safety course")
    async def signup(self, interaction: discord.Interaction):
        """Generate a web signup link with an auth code."""
        discord_id = str(interaction.user.id)
        code = await create_auth_code(discord_id)

        web_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        link = f"{web_url}/auth/code?code={code}&next=/signup"

        await interaction.response.send_message(
            f"Click here to sign up: {link}\n\nThis link expires in 5 minutes.",
            ephemeral=True
        )

    # TODO: Remove this command. Instead we should have an 
    @app_commands.command(name="view-availability", description="View your current availability in UTC and local time")
    async def view_availability(self, interaction: discord.Interaction):
        """Display user's availability in both UTC and local timezone"""
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        user_data = await get_user_profile(user_id)

        if not user_data:
            await interaction.followup.send(
                "You haven't set up your profile yet! Use `/signup` to get started."
            )
            return

        # Parse availability from JSON strings
        availability_str = user_data.get("availability_utc")
        if_needed_str = user_data.get("if_needed_availability_utc")

        availability = json.loads(availability_str) if availability_str else {}
        if_needed = json.loads(if_needed_str) if if_needed_str else {}

        if not availability and not if_needed:
            await interaction.followup.send(
                "You haven't set up your availability yet! Use `/signup` to update your profile."
            )
            return

        name = user_data.get("nickname") or user_data.get("discord_username") or interaction.user.display_name
        user_tz = user_data.get("timezone") or "UTC"

        local_slots = []
        utc_slots = []

        for is_if_needed, time_dict in [(False, availability), (True, if_needed)]:
            for day, slots in time_dict.items():
                day_code = DAY_CODES.get(day, day[0])
                for slot in sorted(slots):
                    hour = int(slot.split(":")[0])
                    utc_slots.append((day_code, slot, is_if_needed))

                    local_day, local_hour = utc_to_local_time(day, hour, user_tz)
                    local_day_code = DAY_CODES.get(local_day, local_day[0])
                    local_slots.append((local_day_code, f"{local_hour:02d}:00", is_if_needed))

        def format_slots(slots):
            if not slots:
                return "None"
            day_order = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4, 'S': 5, 'U': 6}
            sorted_slots = sorted(slots, key=lambda x: (day_order.get(x[0], 0), x[1]))
            return ", ".join(f"{d}{t}{'*' if is_if else ''}" for d, t, is_if in sorted_slots)

        local_str = format_slots(local_slots)
        utc_str = format_slots(utc_slots)

        embed = discord.Embed(
            title=f"Availability for {name}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Profile",
            value=f"**Timezone:** {user_tz}",
            inline=False
        )

        embed.add_field(
            name=f"Local Time ({user_tz})",
            value=f"```\n{local_str}\n```",
            inline=False
        )

        embed.add_field(
            name="UTC Time",
            value=f"```\n{utc_str}\n```",
            inline=False
        )

        embed.set_footer(text="* = if needed | Day codes: M=Mon, T=Tue, W=Wed, R=Thu, F=Fri, S=Sat, U=Sun")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="toggle-facilitator", description="Toggle your facilitator status")
    async def toggle_facilitator_cmd(self, interaction: discord.Interaction):
        """Toggle whether you are marked as a facilitator."""
        user_id = str(interaction.user.id)
        user_data = await get_user_profile(user_id)

        if not user_data:
            await interaction.response.send_message(
                "You haven't signed up yet! Use `/signup` first.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Use core function to toggle (now async)
        new_status = await toggle_facilitator(user_id)

        role_message = ""
        if interaction.guild:
            facilitator_role = discord.utils.get(interaction.guild.roles, name="Facilitator")

            if not facilitator_role:
                try:
                    facilitator_role = await interaction.guild.create_role(
                        name="Facilitator",
                        color=discord.Color.gold(),
                        reason="Created by scheduler bot"
                    )
                    role_message = "\n(Created Facilitator role)"
                except discord.Forbidden:
                    role_message = "\n(Couldn't create/assign role - missing permissions)"
                    facilitator_role = None

            if facilitator_role:
                try:
                    if new_status:
                        await interaction.user.add_roles(facilitator_role)
                        role_message = "\nFacilitator role added"
                    else:
                        await interaction.user.remove_roles(facilitator_role)
                        role_message = "\nFacilitator role removed"
                except discord.Forbidden:
                    role_message = "\n(Couldn't assign role - missing permissions)"

        status_str = "Facilitator" if new_status else "Not a facilitator"
        await interaction.followup.send(
            f"Your status has been updated: **{status_str}**{role_message}"
        )


async def setup(bot):
    await bot.add_cog(EnrollmentCog(bot))
