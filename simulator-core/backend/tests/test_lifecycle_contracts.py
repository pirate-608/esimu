"""Tests for pure lifecycle contracts used by simulator adapters."""

from esimu_core.lifecycle import (
    achievement_details,
    build_initial_character_state,
    build_semester_reset_state,
    normalize_event_entry,
    normalize_forum_post,
    semester_name,
)
from esimu_core.world.catalog import WorldCatalog


def test_initial_character_state_uses_catalog_major_and_course_data() -> None:
    catalog = WorldCatalog("demo-campus")
    assignment = catalog.major_assignment("GEN")
    assert assignment is not None

    state = build_initial_character_state(
        username="测试玩家",
        major_info=assignment["major_info"],
        course_plan=assignment["course_plan"],
        initial_courses=assignment["initial_courses"],
        stat_defaults={"energy": 100, "sanity": 100, "reputation": 0},
        allocated_stats={"iq": 80, "eq": 70, "luck": 75, "charm": 75},
        initial_gold=120,
    )

    assert state.stats_update["username"] == "测试玩家"
    assert state.stats_update["major"] == "通识探索"
    assert state.stats_update["major_abbr"] == "GEN"
    assert state.stats_update["iq"] == 80
    assert state.stats_update["initial_iq"] == 80
    assert state.stats_update["gold"] == 120
    assert state.courses_mastery == {"intro": 0, "methods": 0, "writing": 0}
    assert state.course_states == {"intro": 1, "methods": 1, "writing": 1}
    assert state.summary["courses"][0]["id"] == "intro"


def test_semester_reset_state_recovers_energy_and_names_period() -> None:
    courses = [{"id": "capstone", "name": "Capstone", "credits": 4}]

    state = build_semester_reset_state(
        semester_idx=9,
        courses=courses,
        current_energy=20,
        energy_default=100,
        energy_minimum=0,
    )

    assert semester_name(2) == "大一春夏"
    assert state.stats_update["semester"] == "延毕学期 9"
    assert state.stats_update["energy"] == 60
    assert state.stats_update["exam_completed"] == 0
    assert state.courses_mastery == {"capstone": 0}
    assert state.course_states == {"capstone": 1}
    assert state.summary["energy_recovery"] == {"before": 20, "after": 60}


def test_achievement_details_normalize_dict_and_missing_codes() -> None:
    details = achievement_details(
        ["gpa_king", "LEGACY"],
        {
            "gpa_king": {
                "name": "卷王之王",
                "desc": "GPA 达标",
                "icon": "👑",
            }
        },
    )

    assert details == [
        {
            "code": "gpa_king",
            "name": "卷王之王",
            "desc": "GPA 达标",
            "icon": "👑",
        },
        {
            "code": "LEGACY",
            "name": "LEGACY",
            "desc": "",
            "icon": "🏅",
        },
    ]


def test_content_result_normalizers_keep_adapter_shapes() -> None:
    event = normalize_event_entry(
        {
            "id": "evt_1",
            "title": "摊位前",
            "description": "有人递来传单。",
            "options": [{"text": "看看"}],
        }
    )

    assert event == {
        "id": "evt_1",
        "title": "摊位前",
        "desc": "有人递来传单。",
        "options": [{"text": "看看"}],
    }
    assert normalize_forum_post({"content": "今日份校园笑话"}, "fallback") == (
        "今日份校园笑话"
    )
    assert normalize_forum_post({}, "fallback") == "fallback"
