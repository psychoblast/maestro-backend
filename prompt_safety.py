"""
R-23 — Prompt injection mitigation (v1).

Sanitizes user-controlled strings before interpolation into LLM prompts.
Primary threat: newline-based injection ("\\nIgnore above instructions…").
"""
import re

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize_for_prompt(value: str, max_len: int = 200) -> str:
    """Strip newlines + control chars; truncate to max_len."""
    if not isinstance(value, str):
        value = str(value)
    # Collapse all newlines / carriage-returns to a single space
    value = value.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    # Remove remaining control characters (keep tabs as space for readability)
    value = value.replace("\t", " ")
    value = _CONTROL_CHAR_RE.sub("", value)
    # Collapse multiple spaces
    value = re.sub(r" {2,}", " ", value)
    return value.strip()[:max_len]
