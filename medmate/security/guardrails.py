"""Security guardrails for the ADK agent."""

import re
from typing import Optional, Any
from medmate.security.pii import redact_pii


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


class ADKCallbacks:
    """Callbacks for ADK agent security hooks."""

    def __init__(self):
        self.safety = SafetyGuardrail()

    def before_model_callback(self, request: dict[str, Any]) -> dict[str, Any]:
        """Called before the model is invoked.

        Checks for unsafe medical advice requests and PII.
        """
        messages = request.get("messages", [])
        if not messages:
            return request

        # Get the latest user message
        last_msg = messages[-1] if messages else {}
        user_text = last_msg.get("content", "")

        # Check for safety violations
        if self.safety.is_unsafe_request(user_text):
            # Return a response that bypasses the model
            request["_safety_intercept"] = True
            request["_safety_response"] = self.safety.get_safe_response()
            return request

        # Check for and redact PII
        redacted, found = redact_pii(user_text)
        if found:
            # Log PII detection but don't block; allow the agent to proceed
            # In production, you'd log this for audit purposes
            request["_pii_detected"] = found
            last_msg["content"] = redacted

        return request

    def before_tool_callback(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Called before a tool is executed.

        Validates tool arguments and requires confirmation for destructive operations.
        """
        tool_name = tool_call.get("name", "")
        args = tool_call.get("arguments", {})

        # Validate arguments exist
        if not args:
            tool_call["_validation_error"] = "No arguments provided"
            return tool_call

        # For destructive tools (remove_medication), flag for confirmation
        if tool_name == "remove_medication":
            med_name = args.get("name")
            if not med_name:
                tool_call["_validation_error"] = "Medication name required"
                return tool_call
            tool_call["_requires_confirmation"] = True
            tool_call["_confirmation_message"] = f"About to remove '{med_name}' from your medications. Is this correct?"

        return tool_call

    def after_model_callback(self, response: dict[str, Any]) -> dict[str, Any]:
        """Called after the model generates a response.

        Appends medical disclaimer and ensures safety messages are included.
        """
        # Append disclaimer to all model responses
        disclaimer = "\n\n---\n⚠️ **Important:** This tool is for personal organization only, not medical advice. Always consult your healthcare provider before making medication changes."

        content = response.get("content", "")
        if isinstance(content, str):
            response["content"] = content + disclaimer
        elif isinstance(content, list):
            # If content is a list of message parts
            if content and isinstance(content[-1], dict):
                if "text" in content[-1]:
                    content[-1]["text"] += disclaimer
            else:
                response["content"].append({"type": "text", "text": disclaimer})

        return response
