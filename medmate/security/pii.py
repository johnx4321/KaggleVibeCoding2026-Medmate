"""PII detection and redaction."""

import re
from typing import Optional


class PIIRedactor:
    """Detect and redact personally identifiable information."""

    # Patterns for common PII
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b",
        "ssn": r"\b(?!000|666|9\d{2})\d{3}-?\d{2}-?\d{4}\b",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "date_of_birth": r"\b(19|20)\d{2}[/-](0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])\b",
    }

    def redact(self, text: str) -> tuple[str, list[str]]:
        """Redact PII from text.

        Returns:
            (redacted_text, list of found PII types)
        """
        found_types = []
        redacted = text

        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                found_types.append(pii_type)
                redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)

        return redacted, found_types

    def contains_pii(self, text: str) -> bool:
        """Check if text contains any PII."""
        _, found = self.redact(text)
        return len(found) > 0


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Convenience function to redact PII."""
    redactor = PIIRedactor()
    return redactor.redact(text)


def contains_pii(text: str) -> bool:
    """Check if text contains PII."""
    redactor = PIIRedactor()
    return redactor.contains_pii(text)
