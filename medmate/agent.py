"""MedMate ADK Agent - Multi-agent medication manager.

Coordinator + sub-agents (Intake, Interaction Checker, Scheduler)
with MCP integration and security guardrails.
"""

import os
import logging
from typing import Any, Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from medmate.security.guardrails import ADKCallbacks
from medmate.tools import profile_tools, schedule_tools
from medmate.sub_agents import intake_agent, interaction_agent, scheduler_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize security callbacks
callbacks = ADKCallbacks()


def _create_root_agent() -> LlmAgent:
    """Create the root coordinator agent."""

    # Root agent tools - minimal, mostly routing
    tools = [
        FunctionTool(func=profile_tools.get_profile),
    ]

    instruction = """You are MedMate, a personal medication organizer and care assistant.

Your role:
1. Help users track their medications (add, remove, list)
2. Check for drug interactions among their medications
3. Build and manage medication schedules
4. Provide reminders and organize their care

IMPORTANT: You are NOT a doctor or pharmacist. For medical advice, dosage decisions,
or any health-related guidance, always defer to healthcare professionals.

You have access to specialist sub-agents:
- Intake Agent: Manages medication profiles (add/remove/list meds, allergies, conditions)
- Interaction Agent: Checks for drug-drug interactions and safety warnings
- Scheduler Agent: Builds medication schedules and reminders

For user requests about medications, route to the appropriate sub-agent.
Always be clear about your limitations and encourage consultation with healthcare providers."""

    root = LlmAgent(
        name="medmate_coordinator",
        instruction=instruction,
        model="gemini-2.0-flash",
        tools=tools,
        sub_agents=[
            intake_agent.create_intake_agent(),
            interaction_agent.create_interaction_agent(),
            scheduler_agent.create_scheduler_agent(),
        ],
        # Security callbacks
        before_model_callback=callbacks.before_model_callback,
        before_tool_callback=callbacks.before_tool_callback,
        after_model_callback=callbacks.after_model_callback,
    )

    return root


# Lazy initialization
_root_agent: Optional[LlmAgent] = None


def get_root_agent() -> LlmAgent:
    """Get or create the root agent (lazy init)."""
    global _root_agent
    if _root_agent is None:
        _root_agent = _create_root_agent()
    return _root_agent


# Export for ADK framework
root_agent = get_root_agent()
