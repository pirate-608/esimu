"""Pure runtime state DTOs for simulator adapters.

Adapters translate framework-specific storage models into these plain data
objects before calling runtime helpers. The DTOs intentionally avoid Pydantic
and infrastructure imports so they can be reused by different hosts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def dict_from_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow plain-dict copy from a possibly missing mapping."""
    return dict(value or {})


@dataclass(frozen=True)
class RuntimeCourseState:
    """Course mastery and strategy state for one runtime snapshot."""

    mastery: dict[str, Any] = field(default_factory=dict)
    states: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mappings(
        cls,
        mastery: Mapping[str, Any] | None = None,
        states: Mapping[str, Any] | None = None,
    ) -> "RuntimeCourseState":
        """Build course state from storage-layer mappings."""
        return cls(
            mastery=dict_from_mapping(mastery),
            states=dict_from_mapping(states),
        )


@dataclass(frozen=True)
class RuntimeStats:
    """Plain player stats with helpers for common persisted fields."""

    values: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None = None) -> "RuntimeStats":
        """Build stats from a storage-layer mapping."""
        return cls(dict_from_mapping(values))

    def get_int(self, key: str, default: int = 0) -> int:
        """Read an integer stat while tolerating stringly persisted values."""
        try:
            return int(self.values.get(key, default))
        except (TypeError, ValueError):
            return default


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Complete plain runtime snapshot used by payload helpers."""

    stats: RuntimeStats = field(default_factory=RuntimeStats)
    courses: RuntimeCourseState = field(default_factory=RuntimeCourseState)
    relax_cooldowns: dict[str, int] = field(default_factory=dict)
    semester_duration: int = 360
    dingtalk_state: dict[str, Any] = field(default_factory=dict)
    items_state: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mappings(
        cls,
        *,
        stats: Mapping[str, Any] | None = None,
        courses: Mapping[str, Any] | None = None,
        course_states: Mapping[str, Any] | None = None,
        relax_cooldowns: Mapping[str, int] | None = None,
        semester_duration: int = 360,
        dingtalk_state: Mapping[str, Any] | None = None,
        items_state: Mapping[str, Any] | None = None,
    ) -> "RuntimeSnapshot":
        """Build a runtime snapshot from adapter-provided mappings."""
        return cls(
            stats=RuntimeStats.from_mapping(stats),
            courses=RuntimeCourseState.from_mappings(courses, course_states),
            relax_cooldowns=dict(relax_cooldowns or {}),
            semester_duration=int(semester_duration),
            dingtalk_state=dict_from_mapping(dingtalk_state),
            items_state=dict_from_mapping(items_state),
        )

