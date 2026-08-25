"""Pure stat-effect and feedback formatting rules.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

This module models bounded stat changes without knowing where stats are stored.
Application adapters can apply the returned values to Redis, a database, a
single-player save file, or a test fixture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping


PositiveEndpoint = Literal["max", "min", "none"]


@dataclass(frozen=True)
class StatBounds:
    """Numeric bounds and good endpoint metadata for one stat."""

    minimum: int = 0
    maximum: int = 200
    positive_endpoint: PositiveEndpoint = "max"


@dataclass(frozen=True)
class StatChange:
    """A user-facing stat delta entry."""

    field: str
    label: str
    delta: int | float
    value: int | float | None = None

    def as_dict(self) -> dict[str, int | float | str]:
        """Serialize the change in the shape expected by feedback modals."""
        payload: dict[str, int | float | str] = {
            "field": self.field,
            "label": self.label,
            "delta": self.delta,
        }
        if self.value is not None:
            payload["value"] = self.value
        return payload


@dataclass(frozen=True)
class BoundedDeltaResult:
    """Result of applying one bounded numeric stat delta."""

    value: int
    actual_delta: int
    overflow_units: int
    change: StatChange | None


@dataclass(frozen=True)
class OverflowTransferResult:
    """Result of redistributing relax-only overflow to useful stats."""

    stats: dict[str, int]
    changes: tuple[StatChange, ...]
    transferred_units: int


def safe_int(value: object, default: int = 0) -> int:
    """Convert loose stored values to int with a fallback."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def label_for(field: str, labels: Mapping[str, str] | None = None) -> str:
    """Resolve a display label while tolerating incomplete metadata."""
    return (labels or {}).get(field, field)


def clamp_stat(value: int, bounds: StatBounds) -> int:
    """Clamp a stat value to its configured bounds."""
    return max(bounds.minimum, min(bounds.maximum, value))


def feedback_change(
    field: str,
    delta: int | float,
    labels: Mapping[str, str] | None = None,
    value: int | float | None = None,
) -> StatChange:
    """Create a feedback change entry using theme-provided stat labels."""
    return StatChange(field=field, label=label_for(field, labels), delta=delta, value=value)


def positive_relax_overflow_units(
    field: str,
    requested_delta: int,
    actual_delta: int,
    bounds_by_field: Mapping[str, StatBounds],
) -> int:
    """Calculate relax-only benefit lost to a stat's good endpoint."""
    bounds = bounds_by_field.get(field, StatBounds())
    if bounds.positive_endpoint == "min" and requested_delta < 0:
        return max(0, abs(requested_delta) - max(0, -actual_delta))
    if bounds.positive_endpoint == "max" and requested_delta > 0:
        return max(0, requested_delta - max(0, actual_delta))
    return 0


def apply_bounded_delta(
    stats: Mapping[str, object],
    field: str,
    delta: int,
    bounds_by_field: Mapping[str, StatBounds],
    labels: Mapping[str, str] | None = None,
) -> BoundedDeltaResult:
    """Apply one bounded stat delta to a snapshot and report actual impact."""
    current_value = safe_int(stats.get(field))
    bounds = bounds_by_field.get(field, StatBounds())
    new_value = clamp_stat(current_value + delta, bounds)
    actual_delta = new_value - current_value
    overflow = positive_relax_overflow_units(
        field,
        requested_delta=delta,
        actual_delta=actual_delta,
        bounds_by_field=bounds_by_field,
    )
    change = None
    if actual_delta:
        change = feedback_change(field, actual_delta, labels, new_value)
    return BoundedDeltaResult(
        value=new_value,
        actual_delta=actual_delta,
        overflow_units=overflow,
        change=change,
    )


def apply_delta_to_snapshot(
    stats: Mapping[str, object],
    field: str,
    delta: int,
    bounds_by_field: Mapping[str, StatBounds],
    labels: Mapping[str, str] | None = None,
) -> tuple[dict[str, int], BoundedDeltaResult]:
    """Return a copied snapshot with one bounded stat delta applied."""
    next_stats = {key: safe_int(value) for key, value in stats.items()}
    result = apply_bounded_delta(next_stats, field, delta, bounds_by_field, labels)
    next_stats[field] = result.value
    return next_stats, result


def transfer_relax_overflow(
    stats: Mapping[str, object],
    overflow_units: int,
    bounds_by_field: Mapping[str, StatBounds],
    labels: Mapping[str, str] | None = None,
    targets: tuple[str, ...] = ("energy", "sanity", "charm"),
    transfer_cap: int = 20,
    charm_transfer_cap: int = 1,
) -> OverflowTransferResult:
    """Redistribute relax-only overflow to still-useful positive stats."""
    next_stats = {key: safe_int(value) for key, value in stats.items()}
    remaining = min(max(0, overflow_units), transfer_cap)
    charm_transferred = 0
    changes: list[StatChange] = []

    for field in targets:
        if remaining <= 0:
            break
        current_value = safe_int(next_stats.get(field))
        bounds = bounds_by_field.get(field, StatBounds())
        room = max(0, bounds.maximum - current_value)
        if room <= 0:
            continue

        field_cap = remaining
        if field == "charm":
            field_cap = min(field_cap, max(0, charm_transfer_cap - charm_transferred))
        delta = min(remaining, room, field_cap)
        if delta <= 0:
            continue

        new_value = clamp_stat(current_value + delta, bounds)
        actual_delta = new_value - current_value
        if actual_delta <= 0:
            continue
        next_stats[field] = new_value
        if field == "charm":
            charm_transferred += actual_delta
        remaining -= actual_delta
        changes.append(feedback_change(field, actual_delta, labels, new_value))

    return OverflowTransferResult(
        stats=next_stats,
        changes=tuple(changes),
        transferred_units=sum(int(change.delta) for change in changes),
    )

