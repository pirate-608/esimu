"""Pure automatic-content scheduling decisions for runtime adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import random
from typing import Any


@dataclass(frozen=True)
class ContentScheduleDecision:
    """Automatic content work due after one completed game tick."""

    event_due: bool = False
    messenger_due: bool = False


def scheduled_content_decision(
    *,
    tick_count: int,
    is_running: bool,
    exam_completed: bool,
    ended: bool,
    has_active_event: bool,
    random_event_config: Mapping[str, Any],
    messenger_config: Mapping[str, Any],
    random_value: Callable[[], float] = random.random,
) -> ContentScheduleDecision:
    """Return whether event and messenger generation are due on this tick."""
    if tick_count <= 0 or not is_running or exam_completed or ended:
        return ContentScheduleDecision()
    event_due = not has_active_event and _schedule_matches(
        tick_count, random_event_config, random_value
    )
    messenger_due = _schedule_matches(
        tick_count, messenger_config, random_value
    )
    return ContentScheduleDecision(
        event_due=event_due,
        messenger_due=messenger_due,
    )


def _schedule_matches(
    tick_count: int,
    config: Mapping[str, Any],
    random_value: Callable[[], float],
) -> bool:
    try:
        interval = int(config.get("check_interval_ticks", 0) or 0)
        probability = float(config.get("trigger_probability", 0) or 0)
    except (TypeError, ValueError):
        return False
    if interval <= 0 or tick_count % interval != 0:
        return False
    return random_value() < max(0.0, min(1.0, probability))
