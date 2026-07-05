"""Interaction Agent - checks for drug interactions."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, McpToolset
from medmate.mcp_interaction_handler import check_interactions_local


def create_interaction_agent() -> LlmAgent:
    """Create the interaction checker specialist agent."""

    # For now, use a local function instead of full MCP integration
    # (will work without MCP server running)
    tools = [
        FunctionTool(
            func=check_interactions_local,
            name="check_interactions",
            description="Check for drug-drug interactions among medications",
        ),
    ]

    instruction = """You are the Drug Interaction Specialist for MedMate.

Your job is to:
1. Check for interactions between medications the user is taking
2. Explain interaction severity and implications
3. Recommend consulting their pharmacist or doctor
4. Help them understand medication safety

When users ask about interactions, use the check_interactions tool.
Always emphasize the importance of consulting healthcare professionals."""

    return LlmAgent(
        name="Interaction Agent",
        instruction=instruction,
        model="gemini-2.0-flash",
        tools=tools,
    )
