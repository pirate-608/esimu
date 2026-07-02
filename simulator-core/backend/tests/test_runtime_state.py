"""Tests for pure runtime state DTOs."""

from esimu_core.runtime.state import RuntimeSnapshot, RuntimeStats


def test_runtime_stats_coerce_int_fields() -> None:
    stats = RuntimeStats.from_mapping({"semester_idx": "2", "broken": "x"})

    assert stats.get_int("semester_idx") == 2
    assert stats.get_int("broken", 7) == 7
    assert stats.get_int("missing", 3) == 3


def test_runtime_snapshot_copies_adapter_mappings() -> None:
    raw_stats = {"elapsed_game_time": "12"}
    raw_courses = {"C1": "20"}
    raw_states = {"C1": "2"}

    snapshot = RuntimeSnapshot.from_mappings(
        stats=raw_stats,
        courses=raw_courses,
        course_states=raw_states,
        relax_cooldowns={"walk": 3},
        semester_duration=100,
        dingtalk_state={"contacts": {}},
        items_state={"owned": []},
    )
    raw_stats["elapsed_game_time"] = "99"

    assert snapshot.stats.values["elapsed_game_time"] == "12"
    assert snapshot.courses.mastery == {"C1": "20"}
    assert snapshot.courses.states == {"C1": "2"}
    assert snapshot.relax_cooldowns == {"walk": 3}
    assert snapshot.semester_duration == 100
    assert snapshot.dingtalk_state == {"contacts": {}}
    assert snapshot.items_state == {"owned": []}

