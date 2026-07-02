"""Tick timing calculations for simulator runtime adapters.

The helpers here are pure arithmetic: adapters provide the resolved balance
interval and player speed, then decide how to sleep or persist elapsed time.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TickTiming:
    """Sleep and elapsed-time values for one runtime tick."""

    interval_seconds: int
    speed_multiplier: float
    sleep_seconds: float
    elapsed_increment: int


def _positive_int(value: object, default: int = 3) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)


def _positive_float(value: object, default: float = 1.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = default
    return parsed if parsed > 0 else default


def tick_timing(
    tick_interval_seconds: object,
    speed_multiplier: object = 1.0,
) -> TickTiming:
    """Return real-time sleep and virtual elapsed increment for one tick."""
    interval = _positive_int(tick_interval_seconds)
    speed = _positive_float(speed_multiplier)
    return TickTiming(
        interval_seconds=interval,
        speed_multiplier=speed,
        sleep_seconds=interval / speed,
        elapsed_increment=interval,
    )

