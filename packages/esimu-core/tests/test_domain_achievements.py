"""Tests for declarative achievement conditions."""

from esimu_core.domain.achievements import (
    achievement_condition_issues,
    evaluate_achievement_condition,
    newly_unlocked_achievement_codes,
)


def test_all_and_any_conditions_evaluate_runtime_sources() -> None:
    all_condition = {
        "all": [
            {"scope": "stat", "key": "eq", "op": "gte", "value": 90},
            {
                "scope": "action",
                "key": "messenger_round",
                "op": "gte",
                "value": 3,
            },
        ]
    }
    any_condition = {
        "any": [
            {"scope": "session", "key": "failed_count", "op": "gte", "value": 2},
            {"scope": "stat", "key": "gpa", "op": "gt", "value": 4.0},
        ]
    }

    assert evaluate_achievement_condition(
        all_condition,
        stats={"eq": 95},
        actions={"messenger_round": 3},
        session={},
    )
    assert evaluate_achievement_condition(
        any_condition,
        stats={"gpa": "4.2"},
        actions={},
        session={"failed_count": 0},
    )


def test_invalid_condition_reports_author_errors() -> None:
    issues = achievement_condition_issues(
        {
            "all": [
                {"scope": "stat", "key": "missing", "op": "wat", "value": 1},
            ],
            "any": [],
        },
        stat_ids={"energy"},
    )
    assert issues == ["condition must contain exactly one of all or any"]


def test_newly_unlocked_ignores_existing_and_display_only_entries() -> None:
    config = {
        "existing": {
            "condition": {
                "all": [
                    {"scope": "action", "key": "relax", "op": "gte", "value": 1}
                ]
            }
        },
        "fresh": {
            "condition": {
                "all": [
                    {"scope": "action", "key": "relax", "op": "gte", "value": 1}
                ]
            }
        },
        "manual": {},
    }
    assert newly_unlocked_achievement_codes(
        config,
        unlocked=["existing"],
        stats={},
        actions={"relax": 1},
        session={},
    ) == ["fresh"]
