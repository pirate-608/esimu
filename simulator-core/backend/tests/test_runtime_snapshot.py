"""Tests for runtime payload assembly helpers."""

from esimu_core.runtime.snapshot import (
    RuntimePayloadDefaults,
    RuntimeSnapshotInput,
    build_init_payload,
    build_init_payload_from_snapshot,
    build_new_semester_payload,
    build_tick_payload,
    build_tick_payload_from_snapshot,
)
from esimu_core.runtime.state import RuntimeSnapshot


def test_build_tick_payload_preserves_wire_shape_and_derives_efficiency() -> None:
    payload = build_tick_payload(
        RuntimeSnapshotInput(
            stats={
                "semester_idx": 1,
                "elapsed_game_time": 40,
                "iq": 115,
                "stress": 20,
                "item_bonuses": {"efficiency": 5},
            },
            courses={"C1": 42.0},
            course_states={"C1": 2},
            semester_duration=100,
            relax_cooldowns={"walk": 3},
            iq_default=100,
            stress_default=0,
            efficiency_default=100,
        )
    )

    assert payload["stats"]["efficiency"] == 110
    assert payload["courses"] == {"C1": 42.0}
    assert payload["course_states"] == {"C1": 2}
    assert payload["semester_time_left"] == 60
    assert payload["relax_cooldowns"] == {"walk": 3}


def test_build_init_payload_adds_dingtalk_and_items_state() -> None:
    payload = build_init_payload(
        RuntimeSnapshotInput(
            stats={"elapsed_game_time": 0},
            semester_duration=30,
        ),
        dingtalk_state={"contacts": {}},
        items_state={"owned": []},
    )

    assert payload["data"]["efficiency"] == 100
    assert payload["semester_time_left"] == 30
    assert payload["dingtalk_state"] == {"contacts": {}}
    assert payload["items_state"] == {"owned": []}


def test_snapshot_payload_helpers_accept_runtime_snapshot() -> None:
    snapshot = RuntimeSnapshot.from_mappings(
        stats={
            "elapsed_game_time": 10,
            "iq": 120,
            "stress": 10,
            "course_info_json": "[{}]",
        },
        courses={"C1": 80.0},
        course_states={"C1": 1},
        relax_cooldowns={"cc98": 4},
        semester_duration=90,
        dingtalk_state={"contacts": {"a": {}}},
        items_state={"owned": ["planner"]},
    )
    defaults = RuntimePayloadDefaults(iq=100, stress=0, efficiency=100)

    tick = build_tick_payload_from_snapshot(snapshot, defaults)
    init = build_init_payload_from_snapshot(snapshot, defaults)
    new_semester = build_new_semester_payload(
        snapshot,
        semester_name="第一学期",
        holiday_event={"title": "假期"},
        energy_recovery={"before": 20, "after": 60},
        defaults=defaults,
    )

    assert tick["stats"]["efficiency"] == 115
    assert init["dingtalk_state"] == {"contacts": {"a": {}}}
    assert init["items_state"] == {"owned": ["planner"]}
    assert new_semester["data"]["semester_name"] == "第一学期"
    assert new_semester["data"]["course_info_json"] == "[{}]"
    assert new_semester["data"]["semester_time_left"] == 80
