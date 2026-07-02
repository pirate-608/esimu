"""Cooldown calculations for runtime adapters."""

from __future__ import annotations

import math
from typing import Mapping


def remaining_cooldown_seconds(
    last_used_at: object,
    cooldown_seconds: object,
    now_seconds: object,
) -> int:
    """Return remaining cooldown seconds for one action."""
    if last_used_at is None:
        return 0
    try:
        last_used = float(last_used_at)  # type: ignore[arg-type]
        cooldown = float(cooldown_seconds)  # type: ignore[arg-type]
        now = float(now_seconds)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    if cooldown <= 0:
        return 0
    return math.ceil(max(0.0, cooldown - (now - last_used)))


def build_cooldown_map(
    actions: list[str] | tuple[str, ...],
    timestamps: Mapping[str, object],
    cooldown_seconds_by_action: Mapping[str, object],
    now_seconds: object,
) -> dict[str, int]:
    """Return remaining cooldown seconds keyed by action ID."""
    result: dict[str, int] = {}
    for action in actions:
        result[action] = remaining_cooldown_seconds(
            timestamps.get(action),
            cooldown_seconds_by_action.get(action, 0),
            now_seconds,
        )
    return result

