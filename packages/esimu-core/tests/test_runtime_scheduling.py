"""Tests for automatic event and messenger scheduling."""

from esimu_core.runtime.scheduling import scheduled_content_decision


def test_scheduling_uses_intervals_and_probabilities_once_per_due_target() -> None:
    values = iter([0.1, 0.9])
    decision = scheduled_content_decision(
        tick_count=12,
        is_running=True,
        exam_completed=False,
        ended=False,
        has_active_event=False,
        random_event_config={"check_interval_ticks": 12, "trigger_probability": 0.2},
        messenger_config={"check_interval_ticks": 6, "trigger_probability": 0.2},
        random_value=lambda: next(values),
    )
    assert decision.event_due is True
    assert decision.messenger_due is False


def test_scheduling_stops_with_runtime_and_active_event_gates() -> None:
    stopped = scheduled_content_decision(
        tick_count=10,
        is_running=False,
        exam_completed=False,
        ended=False,
        has_active_event=False,
        random_event_config={"check_interval_ticks": 1, "trigger_probability": 1},
        messenger_config={"check_interval_ticks": 1, "trigger_probability": 1},
        random_value=lambda: 0,
    )
    active = scheduled_content_decision(
        tick_count=10,
        is_running=True,
        exam_completed=False,
        ended=False,
        has_active_event=True,
        random_event_config={"check_interval_ticks": 1, "trigger_probability": 1},
        messenger_config={"check_interval_ticks": 50, "trigger_probability": 1},
        random_value=lambda: 0,
    )
    assert stopped.event_due is stopped.messenger_due is False
    assert active.event_due is active.messenger_due is False
