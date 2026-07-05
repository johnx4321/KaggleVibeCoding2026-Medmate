"""Tests for security guardrails."""

import pytest
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


def test_adk_callbacks_before_model():
    """Test ADK before_model callback."""
    callbacks = ADKCallbacks()
    request = {
        "messages": [
            {"content": "should i stop taking my medication?"}
        ]
    }
    result = callbacks.before_model_callback(request)
    assert "_safety_intercept" in result
    assert result["_safety_intercept"] is True


def test_adk_callbacks_tool_validation():
    """Test ADK before_tool callback."""
    callbacks = ADKCallbacks()
    tool_call = {
        "name": "remove_medication",
        "arguments": {"name": "lisinopril"}
    }
    result = callbacks.before_tool_callback(tool_call)
    assert "_requires_confirmation" in result
