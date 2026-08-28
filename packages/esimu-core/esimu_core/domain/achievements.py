"""Declarative achievement-condition rules for esimu themes.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

Achievement evaluation is intentionally data-only. Adapters provide current
stats, action counters, and session metrics; this module never reads storage or
emits UI messages.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any


ACHIEVEMENT_SCOPES = frozenset({"stat", "action", "session"})
ACHIEVEMENT_OPERATORS = frozenset({"gte", "gt", "lte", "lt", "eq"})
ACHIEVEMENT_SESSION_KEYS = frozenset(
    {"semester_idx", "completed_terms", "failed_count", "term_gpa", "cumulative_gpa"}
)


def achievement_condition_issues(
    condition: Any,
    *,
    stat_ids: set[str] | frozenset[str] | None = None,
) -> list[str]:
    """Return author-facing validation errors for one condition object."""
    if not isinstance(condition, Mapping):
        return ["condition must be an object"]

    groups = [name for name in ("all", "any") if name in condition]
    if len(groups) != 1:
        return ["condition must contain exactly one of all or any"]
    group = groups[0]
    predicates = condition.get(group)
    if not isinstance(predicates, list) or not predicates:
        return [f"condition.{group} must be a non-empty array"]

    issues: list[str] = []
    for index, predicate in enumerate(predicates):
        location = f"condition.{group}[{index}]"
        if not isinstance(predicate, Mapping):
            issues.append(f"{location} must be an object")
            continue
        scope = str(predicate.get("scope") or "").strip()
        key = str(predicate.get("key") or "").strip()
        operator = str(predicate.get("op") or "").strip()
        value = predicate.get("value")
        if scope not in ACHIEVEMENT_SCOPES:
            issues.append(f"{location}.scope must be stat, action, or session")
        if not key:
            issues.append(f"{location}.key is required")
        elif scope == "stat" and stat_ids is not None and key not in stat_ids:
            issues.append(f"{location}.key references unknown stat {key}")
        elif scope == "session" and key not in ACHIEVEMENT_SESSION_KEYS:
            issues.append(f"{location}.key is not a supported session metric")
        if operator not in ACHIEVEMENT_OPERATORS:
            issues.append(f"{location}.op must be gte, gt, lte, lt, or eq")
        if not isinstance(value, str | int | float | bool) or value is None:
            issues.append(f"{location}.value must be a scalar")
    return issues


def evaluate_achievement_condition(
    condition: Any,
    *,
    stats: Mapping[str, Any],
    actions: Mapping[str, Any],
    session: Mapping[str, Any],
) -> bool:
    """Evaluate one validated declarative condition against runtime values."""
    if achievement_condition_issues(condition):
        return False
    assert isinstance(condition, Mapping)
    group = "all" if "all" in condition else "any"
    predicates = condition[group]
    results = [
        _evaluate_predicate(
            predicate,
            stats=stats,
            actions=actions,
            session=session,
        )
        for predicate in predicates
    ]
    return all(results) if group == "all" else any(results)


def newly_unlocked_achievement_codes(
    achievements: Mapping[str, Mapping[str, Any]],
    *,
    unlocked: Sequence[str],
    stats: Mapping[str, Any],
    actions: Mapping[str, Any],
    session: Mapping[str, Any],
) -> list[str]:
    """Return configured achievement codes newly satisfied by current state."""
    existing = {str(code) for code in unlocked}
    result: list[str] = []
    for code, achievement in achievements.items():
        normalized = str(code).strip()
        condition = achievement.get("condition")
        if not normalized or normalized in existing or condition is None:
            continue
        if evaluate_achievement_condition(
            condition,
            stats=stats,
            actions=actions,
            session=session,
        ):
            result.append(normalized)
    return result


def _evaluate_predicate(
    predicate: Mapping[str, Any],
    *,
    stats: Mapping[str, Any],
    actions: Mapping[str, Any],
    session: Mapping[str, Any],
) -> bool:
    scope = str(predicate.get("scope"))
    source = {"stat": stats, "action": actions, "session": session}[scope]
    actual = source.get(str(predicate.get("key")), 0)
    expected = predicate.get("value")
    operator = str(predicate.get("op"))
    left, right = _comparable_values(actual, expected)
    try:
        if operator == "gte":
            return left >= right
        if operator == "gt":
            return left > right
        if operator == "lte":
            return left <= right
        if operator == "lt":
            return left < right
        return left == right
    except TypeError:
        return False


def _comparable_values(actual: Any, expected: Any) -> tuple[Any, Any]:
    if isinstance(expected, Real) and not isinstance(expected, bool):
        try:
            return float(actual), float(expected)
        except (TypeError, ValueError):
            return 0.0, float(expected)
    return actual, expected
