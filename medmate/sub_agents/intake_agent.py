"""Intake Agent - manages user medication profile."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from medmate.tools import profile_tools


def create_intake_agent() -> LlmAgent:
    """Create the intake specialist agent."""

    tools = [
        FunctionTool(func=profile_tools.add_medication),
        FunctionTool(func=profile_tools.remove_medication),
        FunctionTool(func=profile_tools.list_medications),
        FunctionTool(func=profile_tools.add_allergy),
        FunctionTool(func=profile_tools.list_allergies),
        FunctionTool(func=profile_tools.add_condition),
        FunctionTool(func=profile_tools.get_profile),
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
        name="intake_agent",
        instruction=instruction,
        model="gemini-2.0-flash",
        tools=tools,
    )
