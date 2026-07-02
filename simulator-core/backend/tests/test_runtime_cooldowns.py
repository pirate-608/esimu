"""Tests for runtime cooldown calculations."""

from esimu_core.runtime.cooldowns import build_cooldown_map, remaining_cooldown_seconds


def test_remaining_cooldown_handles_missing_or_expired_values() -> None:
    assert remaining_cooldown_seconds(None, 30, 100) == 0
    assert remaining_cooldown_seconds(10, 30, 100) == 0
    assert remaining_cooldown_seconds("bad", 30, 100) == 0


def test_remaining_cooldown_rounds_up_active_values() -> None:
    assert remaining_cooldown_seconds(90.2, 10, 95.8) == 5


def test_build_cooldown_map_returns_all_actions() -> None:
    result = build_cooldown_map(
        ["walk", "cc98", "gym"],
        {"walk": 90, "cc98": 10},
        {"walk": 30, "cc98": 30, "gym": 20},
        100,
    )

    assert result == {"walk": 20, "cc98": 0, "gym": 0}

