"""Tests for runtime tick timing helpers."""

from esimu_core.runtime.clock import tick_timing


def test_tick_timing_uses_interval_for_elapsed_and_speed_for_sleep() -> None:
    timing = tick_timing(7, 2)

    assert timing.interval_seconds == 7
    assert timing.elapsed_increment == 7
    assert timing.sleep_seconds == 3.5
    assert timing.speed_multiplier == 2


def test_tick_timing_coerces_invalid_values_to_safe_defaults() -> None:
    timing = tick_timing("bad", 0)

    assert timing.interval_seconds == 3
    assert timing.elapsed_increment == 3
    assert timing.sleep_seconds == 3
    assert timing.speed_multiplier == 1.0

