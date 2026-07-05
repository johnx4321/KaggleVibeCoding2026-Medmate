"""Security guardrails for the ADK agent.

Callback signatures here must match ADK's actual invocation contract
(see google.adk.flows.llm_flows.base_llm_flow / functions.py), not a
made-up dict-based interface — ADK calls these with specific keyword
arguments and typed objects (LlmRequest/LlmResponse/BaseTool/ToolContext).
"""

import re
import logging
from typing import Optional, Any
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from medmate.security.pii import redact_pii

logger = logging.getLogger(__name__)


class SafetyGuardrail:
    """Prevents the agent from giving definitive medical advice."""

    UNSAFE_PATTERNS = [
        r"should i (take|stop|increase|decrease|change|switch)",
        r"is it safe to",
        r"can i take",
        r"what dosage",
        r"how much should i",
        r"should i (double|triple|halve)",
        r"can i (combine|mix)",
    ]

    SAFE_RESPONSE = (
        "I'm a personal medication organizer, not a medical professional. "
        "For questions about dosages, safety, or medication changes, "
        "please consult your doctor or pharmacist. I can help you track "
        "your medications and check for known interactions between drugs, "
        "but any medical decisions require professional guidance."
    )

    def is_unsafe_request(self, text: str) -> bool:
        """Check if a request is asking for definitive medical advice."""
        text_lower = text.lower()
        for pattern in self.UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def get_safe_response(self) -> str:
        """Get the standard safety disclaimer response."""
        return self.SAFE_RESPONSE


def _latest_user_text(llm_request: LlmRequest) -> str:
    """Extract the text of the most recent user turn from an LlmRequest."""
    for content in reversed(llm_request.contents or []):
        if content.role == "user" and content.parts:
            return "".join(part.text or "" for part in content.parts)
    return ""


class ADKCallbacks:
    """Callbacks for ADK agent security hooks."""

    def __init__(self):
        self.safety = SafetyGuardrail()

    def before_model_callback(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Intercepts unsafe medical-advice requests; redacts PII otherwise.

        Returning an LlmResponse here short-circuits the actual model call.
        Returning None lets the (possibly mutated) request proceed.
        """
        user_text = _latest_user_text(llm_request)
        if not user_text:
            return None

        if self.safety.is_unsafe_request(user_text):
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=self.safety.get_safe_response())],
                )
            )

        # Redact PII in place so it never reaches the model/logs.
        for content in reversed(llm_request.contents or []):
            if content.role == "user" and content.parts:
                for part in content.parts:
                    if part.text:
                        redacted, found = redact_pii(part.text)
                        if found:
                            logger.info(f"Redacted PII types: {found}")
                            part.text = redacted
                break

        return None

    def before_tool_callback(
        self, tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
    ) -> Optional[dict]:
        """Validates tool arguments before execution.

        Returning a dict here short-circuits actual tool execution and is
        used as the tool's result. Returning None lets the tool run normally.
        """
        if tool.name == "remove_medication" and not args.get("name"):
            return {"status": "error", "message": "Medication name required"}
        return None

    def after_model_callback(
        self, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Appends a medical disclaimer to the model's final text response."""
        if llm_response.partial:
            # Skip streaming chunks; only annotate the final response.
            return None

        if not llm_response.content or not llm_response.content.parts:
            return None

        disclaimer = (
            "\n\n---\n⚠️ **Important:** This tool is for personal organization "
            "only, not medical advice. Always consult your healthcare provider "
            "before making medication changes."
        )

        annotated = False
        for part in llm_response.content.parts:
            if part.text:
                part.text += disclaimer
                annotated = True

        return llm_response if annotated else None
