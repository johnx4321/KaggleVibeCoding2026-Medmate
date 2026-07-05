"""Tests for security guardrails."""

import pytest
from types import SimpleNamespace
from google.genai import types as genai_types
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from medmate.security.guardrails import SafetyGuardrail, ADKCallbacks
from medmate.security.pii import PIIRedactor, redact_pii


def test_safety_guardrail_detects_dosage_question():
    """Test that safety guardrail detects medical advice requests."""
    guardrail = SafetyGuardrail()
    assert guardrail.is_unsafe_request("should i increase my dosage?")
    assert guardrail.is_unsafe_request("can i take ibuprofen with lisinopril?")
    assert guardrail.is_unsafe_request("should i stop taking this medication?")


def test_safety_guardrail_allows_safe_requests():
    """Test that safe requests pass through."""
    guardrail = SafetyGuardrail()
    assert not guardrail.is_unsafe_request("list my medications")
    assert not guardrail.is_unsafe_request("add lisinopril to my profile")
    assert not guardrail.is_unsafe_request("check for interactions")


def test_pii_redaction_email():
    """Test PII redaction for email."""
    redactor = PIIRedactor()
    text = "Contact me at john.doe@example.com for details"
    redacted, found = redactor.redact(text)
    assert "REDACTED_EMAIL" in redacted
    assert "email" in found


def test_pii_redaction_phone():
    """Test PII redaction for phone."""
    redactor = PIIRedactor()
    text = "Call me at 555-123-4567"
    redacted, found = redactor.redact(text)
    assert "REDACTED_PHONE" in redacted
    assert "phone" in found


def test_pii_redaction_ssn():
    """Test PII redaction for SSN."""
    redactor = PIIRedactor()
    text = "My SSN is 123-45-6789"
    redacted, found = redactor.redact(text)
    assert "REDACTED_SSN" in redacted
    assert "ssn" in found


def test_pii_convenience_function():
    """Test the convenience redaction function."""
    text = "Email: test@example.com"
    redacted, found = redact_pii(text)
    assert "REDACTED_EMAIL" in redacted
    assert "email" in found


def _make_llm_request(user_text: str) -> LlmRequest:
    """Build a minimal real LlmRequest with a single user turn, matching what ADK passes to before_model_callback."""
    return LlmRequest(
        contents=[
            genai_types.Content(role="user", parts=[genai_types.Part(text=user_text)])
        ]
    )


def test_adk_callbacks_before_model_intercepts_unsafe_request():
    """Unsafe medical-advice requests should short-circuit with a safety response."""
    callbacks = ADKCallbacks()
    request = _make_llm_request("should i stop taking my medication?")
    result = callbacks.before_model_callback(None, request)
    assert result is not None
    assert "consult your doctor" in result.content.parts[0].text.lower()


def test_adk_callbacks_before_model_redacts_pii_in_place():
    """Safe requests should pass through (return None) but have PII redacted in the request."""
    callbacks = ADKCallbacks()
    request = _make_llm_request("my email is john@example.com, list my medications")
    result = callbacks.before_model_callback(None, request)
    assert result is None
    assert "REDACTED_EMAIL" in request.contents[0].parts[0].text


def test_adk_callbacks_tool_validation_blocks_missing_name():
    """Removing a medication without a name should be blocked before execution."""
    callbacks = ADKCallbacks()
    tool = SimpleNamespace(name="remove_medication")
    result = callbacks.before_tool_callback(tool, {}, None)
    assert result is not None
    assert result["status"] == "error"


def test_adk_callbacks_tool_validation_allows_valid_call():
    """A well-formed remove_medication call should proceed (return None)."""
    callbacks = ADKCallbacks()
    tool = SimpleNamespace(name="remove_medication")
    result = callbacks.before_tool_callback(tool, {"name": "lisinopril"}, None)
    assert result is None


def test_adk_callbacks_after_model_appends_disclaimer():
    """Final text responses should get the medical disclaimer appended."""
    callbacks = ADKCallbacks()
    response = LlmResponse(
        content=genai_types.Content(
            role="model", parts=[genai_types.Part(text="Here are your medications.")]
        )
    )
    result = callbacks.after_model_callback(None, response)
    assert result is not None
    assert "not medical advice" in result.content.parts[0].text.lower()
