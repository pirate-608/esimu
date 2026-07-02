"""Regression tests for pure stat-effect rules."""

from esimu_core.domain.effects import (
    StatBounds,
    apply_bounded_delta,
    apply_delta_to_snapshot,
    feedback_change,
    positive_relax_overflow_units,
    transfer_relax_overflow,
)


BOUNDS = {
    "energy": StatBounds(0, 200, "max"),
    "sanity": StatBounds(0, 200, "max"),
    "stress": StatBounds(0, 200, "min"),
    "charm": StatBounds(0, 200, "max"),
}
LABELS = {
    "energy": "精力",
    "sanity": "心态",
    "stress": "压力",
    "charm": "魅力",
}


def test_feedback_change_uses_theme_labels() -> None:
    assert feedback_change("energy", 3, LABELS, 103).as_dict() == {
        "field": "energy",
        "label": "精力",
        "delta": 3,
        "value": 103,
    }


def test_positive_overflow_detects_max_endpoint_loss() -> None:
    overflow = positive_relax_overflow_units(
        "energy",
        requested_delta=15,
        actual_delta=5,
        bounds_by_field=BOUNDS,
    )

    assert overflow == 10


def test_positive_overflow_detects_min_endpoint_loss() -> None:
    overflow = positive_relax_overflow_units(
        "stress",
        requested_delta=-12,
        actual_delta=-2,
        bounds_by_field=BOUNDS,
    )

    assert overflow == 10


def test_apply_delta_to_snapshot_clamps_and_reports_actual_delta() -> None:
    stats, result = apply_delta_to_snapshot(
        {"energy": 198},
        "energy",
        10,
        BOUNDS,
        LABELS,
    )

    assert stats["energy"] == 200
    assert result.actual_delta == 2
    assert result.overflow_units == 8
    assert result.change is not None
    assert result.change.as_dict()["delta"] == 2


def test_apply_bounded_delta_uses_unknown_stat_fallback_bounds() -> None:
    result = apply_bounded_delta({"unknown": 198}, "unknown", 10, {}, {})

    assert result.value == 200
    assert result.actual_delta == 2
    assert result.overflow_units == 8


def test_transfer_relax_overflow_uses_priority_targets_and_caps() -> None:
    result = transfer_relax_overflow(
        {"energy": 195, "sanity": 199, "charm": 100},
        overflow_units=50,
        bounds_by_field=BOUNDS,
        labels=LABELS,
        transfer_cap=20,
        charm_transfer_cap=1,
    )

    assert result.stats["energy"] == 200
    assert result.stats["sanity"] == 200
    assert result.stats["charm"] == 101
    assert result.transferred_units == 7
    assert [change.field for change in result.changes] == [
        "energy",
        "sanity",
        "charm",
    ]


def test_transfer_relax_overflow_skips_full_targets() -> None:
    result = transfer_relax_overflow(
        {"energy": 200, "sanity": 200, "charm": 200},
        overflow_units=20,
        bounds_by_field=BOUNDS,
        labels=LABELS,
    )

    assert result.stats == {"energy": 200, "sanity": 200, "charm": 200}
    assert result.changes == ()
    assert result.transferred_units == 0


