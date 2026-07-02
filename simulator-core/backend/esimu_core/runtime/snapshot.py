"""Frontend runtime payload helpers for simulator adapters.

The helpers return plain dictionaries so adapters can keep their existing wire
contracts while moving repetitive payload assembly out of engine classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def safe_int(value: object, default: int = 0) -> int:
    """Convert loose persisted values to int with a fallback."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def semester_time_left(elapsed_game_time: object, duration_seconds: object) -> int:
    """Return non-negative remaining virtual semester time."""
    try:
        elapsed = int(elapsed_game_time)  # type: ignore[arg-type]
        duration = int(duration_seconds)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        if isinstance(duration_seconds, (int, float)):
            return int(duration_seconds)
        return 360
    return max(0, duration - elapsed)


@dataclass(frozen=True)
class RuntimeSnapshotInput:
    """Inputs needed to build a canonical running-state payload."""

    stats: Mapping[str, Any]
    courses: Mapping[str, Any] = field(default_factory=dict)
    course_states: Mapping[str, Any] = field(default_factory=dict)
    semester_duration: int = 360
    relax_cooldowns: Mapping[str, int] = field(default_factory=dict)
    iq_default: int = 100
    stress_default: int = 0
    efficiency_default: int = 100


def effective_efficiency(
    stats: Mapping[str, Any],
    *,
    iq_default: int = 100,
    stress_default: int = 0,
    efficiency_default: int = 100,
) -> int:
    """Calculate derived efficiency for display-only payloads."""
    iq = safe_int(stats.get("iq"), iq_default)
    stress = safe_int(stats.get("stress"), stress_default)
    item_bonuses = stats.get("item_bonuses")
    efficiency_bonus = (
        safe_int(item_bonuses.get("efficiency"), 0)
        if isinstance(item_bonuses, Mapping)
        else 0
    )
    return max(
        10,
        efficiency_default + (iq - iq_default) - int(stress * 0.5) + efficiency_bonus,
    )


def build_tick_payload(payload_input: RuntimeSnapshotInput) -> dict[str, Any]:
    """Build the existing `tick` payload shape for the reference frontend."""
    stats = dict(payload_input.stats)
    stats["efficiency"] = effective_efficiency(
        stats,
        iq_default=payload_input.iq_default,
        stress_default=payload_input.stress_default,
        efficiency_default=payload_input.efficiency_default,
    )
    return {
        "stats": stats,
        "courses": dict(payload_input.courses),
        "course_states": dict(payload_input.course_states),
        "semester_time_left": semester_time_left(
            stats.get("elapsed_game_time", 0),
            payload_input.semester_duration,
        ),
        "relax_cooldowns": dict(payload_input.relax_cooldowns),
    }


def build_init_payload(
    payload_input: RuntimeSnapshotInput,
    *,
    dingtalk_state: Mapping[str, Any],
    items_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the existing `init` payload shape for the reference frontend."""
    tick_payload = build_tick_payload(payload_input)
    return {
        "data": tick_payload["stats"],
        "courses": tick_payload["courses"],
        "course_states": tick_payload["course_states"],
        "semester_time_left": tick_payload["semester_time_left"],
        "relax_cooldowns": tick_payload["relax_cooldowns"],
        "dingtalk_state": dict(dingtalk_state),
        "items_state": dict(items_state),
    }
