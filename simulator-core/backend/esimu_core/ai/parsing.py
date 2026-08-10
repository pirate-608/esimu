"""Defensive parsing helpers for model-generated content."""

from __future__ import annotations

import json
from typing import Any


def json_object_from_text(content: object) -> dict[str, Any]:
    """Extract one JSON object from plain text or a fenced response."""
    if not isinstance(content, str) or not content.strip():
        return {}
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start : end + 1]
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def string_list(value: object, *, limit: int | None = None) -> list[str]:
    """Return non-empty strings from an untrusted model value."""
    if not isinstance(value, list):
        return []
    result = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return result[:limit] if limit is not None else result


def dict_list(value: object, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Return dictionary entries from an untrusted model value."""
    if not isinstance(value, list):
        return []
    result = [item for item in value if isinstance(item, dict)]
    return result[:limit] if limit is not None else result
