"""Tests for authoring-time theme pack contract validation."""

from __future__ import annotations

import json
from pathlib import Path

from esimu_core.world.theme_contract import validate_theme_pack


def test_zju_and_demo_theme_contracts_pass() -> None:
    lab_root = Path(__file__).resolve().parents[3]

    assert validate_theme_pack(lab_root / "themes" / "zju") == []
    assert validate_theme_pack(lab_root / "themes" / "demo-campus") == []


def test_theme_contract_reports_missing_required_files(tmp_path: Path) -> None:
    theme = tmp_path / "themes" / "empty"
    theme.mkdir(parents=True)

    issues = validate_theme_pack(theme)
    messages = [issue.format() for issue in issues]

    assert any("world directory is required" in message for message in messages)
    assert any("theme.json" in message for message in messages)
    assert any("story.json" in message for message in messages)
    assert any("prompts.json" in message for message in messages)


def test_theme_contract_reports_course_field_errors(tmp_path: Path) -> None:
    theme = tmp_path / "themes" / "broken-campus"
    world = theme / "world"
    courses = world / "courses"
    courses.mkdir(parents=True)

    _write_json(
        theme / "theme.json",
        {
            "theme_id": "broken-campus",
            "display_name": "Broken Campus",
            "terms": {
                "campus": "Broken Campus",
                "forum": "Forum",
                "messenger": "Messenger",
                "player": "Player",
                "semester": "Term",
                "course": "Course",
                "item": "Item",
            },
        },
    )
    _write_json(
        theme / "story.json",
        {
            "prologue": {
                "diary_title": "Diary",
                "dedication_lines": ["For everyone."],
                "diary_pages": [["Line one."]],
                "scenes": [{"from_line": 0, "image": "hero.webp", "tone": "morning"}],
            },
            "endings": {
                "failure_date": "2026",
                "failure_title_lines": ["Failed"],
                "failure_default_reason": "Reason",
                "failure_note": "Note",
                "graduation_kicker": "Kicker",
                "graduation_title": "Title",
                "graduation_line_low_gpa": "Low",
                "graduation_line_high_gpa": "High",
                "graduation_summary_label": "Summary",
                "graduation_fallback_summary": "Fallback",
                "graduation_background_images": ["hero.webp"],
            },
        },
    )
    _write_json(
        theme / "prompts.json",
        {
            "campus_context": "Campus",
            "forum_name": "Forum",
            "messenger_name": "Messenger",
            "forum_batch_instruction": "Make forum posts.",
            "random_event_instruction": "Make events.",
            "messenger_batch_instruction": "Make messages.",
            "private_chat_instruction": "Make private chat.",
            "player_identity_template": "{username} {major} {semester} {charm_label} {charm}",
            "messenger_scene_template": "{semester} {scene}",
            "messenger_open_template": "{username}",
            "graduation_instruction": "Make summary.",
        },
    )
    _write_json(
        world / "stat_definitions.json",
        {
            "initial_budget": 100,
            "stats": [
                {
                    "id": "iq",
                    "label": "IQ",
                    "default": 100,
                    "min": 0,
                    "max": 200,
                    "allocatable": True,
                    "show_in_character_create": True,
                }
            ],
        },
    )
    _write_json(world / "game_balance.json", _minimal_balance())
    _write_json(world / "items.json", {"economy": {}, "items": []})
    _write_json(world / "majors.json", [{"id": "GEN", "name": "General"}])
    _write_json(world / "achievements.json", [{"code": "first", "name": "First", "desc": "Done"}])
    _write_json(
        world / "event_library.json",
        [{"title": "Event", "desc": "Desc", "options": [{"text": "Go", "effects": {}}]}],
    )
    _write_json(world / "cc98_library.json", [{"content": "Forum post"}])
    _write_json(
        world / "characters.json",
        [{"name": "Alex", "role": "friend", "description": "A friend."}],
    )
    _write_json(
        world / "graduation_comments.json",
        {"comments": [{"min_gpa": 0, "texts": ["Done."]}]},
    )
    _write_json(courses / "GEN.json", [{"id": "intro", "name": "Intro"}])

    issues = validate_theme_pack(theme)
    messages = [issue.format() for issue in issues]

    assert any("GEN.json" in message and "credits must be numeric" in message for message in messages)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _minimal_balance() -> dict[str, object]:
    return {
        "tick": {"interval_seconds": 3},
        "events": {
            "random_event": {"check_interval_ticks": 1, "trigger_probability": 0.1},
            "dingtalk": {"check_interval_ticks": 1, "trigger_probability": 0.1},
        },
        "game_over": {"sanity_threshold": 0},
    }
