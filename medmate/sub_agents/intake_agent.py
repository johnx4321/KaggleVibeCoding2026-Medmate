"""Intake Agent - manages user medication profile."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from medmate.tools import profile_tools


def create_intake_agent() -> LlmAgent:
    """Create the intake specialist agent."""

    tools = [
        FunctionTool(
            func=profile_tools.add_medication,
            name="add_medication",
            description="Add a medication to the user's profile",
        ),
        FunctionTool(
            func=profile_tools.remove_medication,
            name="remove_medication",
            description="Remove a medication from the user's profile",
        ),
        FunctionTool(
            func=profile_tools.list_medications,
            name="list_medications",
            description="List all medications in the user's profile",
        ),
        FunctionTool(
            func=profile_tools.add_allergy,
            name="add_allergy",
            description="Record an allergy",
        ),
        FunctionTool(
            func=profile_tools.list_allergies,
            name="list_allergies",
            description="List all recorded allergies",
        ),
        FunctionTool(
            func=profile_tools.add_condition,
            name="add_condition",
            description="Record a medical condition",
        ),
        FunctionTool(
            func=profile_tools.get_profile,
            name="get_profile",
            description="Get the full profile summary",
        ),
    ]

    instruction = """You are the Intake Specialist for MedMate.

Your job is to help users manage their medication profile:
- Add medications with dosage and frequency
- Remove medications when no longer needed
- Record allergies and medical conditions
- Provide a summary of their current profile

When users ask about adding or managing their medications, use the appropriate tools.
Always confirm what you're doing and provide clear feedback."""

    return LlmAgent(
        name="Intake Agent",
        instruction=instruction,
        model="gemini-2.0-flash",
        tools=tools,
    )
