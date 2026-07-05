"""Scheduler Agent - manages medication schedules."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from medmate.tools import schedule_tools


def create_scheduler_agent() -> LlmAgent:
    """Create the scheduler specialist agent."""

    tools = [
        FunctionTool(
            func=schedule_tools.build_medication_schedule,
            name="build_schedule",
            description="Build a daily medication schedule from current medications",
        ),
        FunctionTool(
            func=schedule_tools.get_next_doses,
            name="get_next_doses",
            description="Get upcoming doses in the next N hours",
        ),
        FunctionTool(
            func=schedule_tools.export_schedule_ics,
            name="export_schedule",
            description="Export medication schedule as iCalendar format",
        ),
    ]

    instruction = """You are the Scheduler Specialist for MedMate.

Your job is to:
1. Build medication schedules based on dosing frequencies
2. Help users plan their medication timing
3. Provide reminders for upcoming doses
4. Export schedules they can use in their calendar

When users ask about their medication schedule or timing, use the scheduling tools.
Always consider their daily routine and typical wake times."""

    return LlmAgent(
        name="Scheduler Agent",
        instruction=instruction,
        model="gemini-2.0-flash",
        tools=tools,
    )
