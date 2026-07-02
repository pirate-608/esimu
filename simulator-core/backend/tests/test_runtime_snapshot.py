"""Tests for runtime payload assembly helpers."""

from esimu_core.runtime.snapshot import RuntimeSnapshotInput, build_init_payload, build_tick_payload


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

