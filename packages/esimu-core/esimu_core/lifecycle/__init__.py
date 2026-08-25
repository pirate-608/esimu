"""Reusable lifecycle contracts for simulator adapters.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

This module owns deterministic setup and transition payload shaping that should
survive framework themes. It intentionally avoids Redis, SQLAlchemy, FastAPI,
WebSocket objects, and reference-app schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from esimu_core.content import (
    normalize_event_entry as normalize_content_event_entry,
    normalize_forum_post as normalize_content_forum_post,
)
from esimu_core.domain.semester import recover_toward_baseline

SEMESTER_NAMES = (
    "大一秋冬",
    "大一春夏",
    "大二秋冬",
    "大二春夏",
    "大三秋冬",
    "大三春夏",
    "大四秋冬",
    "大四春夏",
)


@dataclass(frozen=True)
class InitialCharacterState:
    """State fragments needed by an adapter to create a fresh game."""

    stats_update: dict[str, Any]
    courses_mastery: dict[str, int]
    course_states: dict[str, int]
    summary: dict[str, Any]


@dataclass(frozen=True)
class SemesterResetState:
    """State fragments needed after advancing into a new semester."""

    stats_update: dict[str, Any]
    courses_mastery: dict[str, int]
    course_states: dict[str, int]
    summary: dict[str, Any]


@dataclass(frozen=True)
class AchievementDetail:
    """Normalized achievement detail for UI and save payloads."""

    code: str
    name: str
    desc: str
    icon: str

    def as_dict(self) -> dict[str, str]:
        """Return the JSON-friendly shape used by reference adapters."""
        return {
            "code": self.code,
            "name": self.name,
            "desc": self.desc,
            "icon": self.icon,
        }


def semester_name(semester_idx: int) -> str:
    """Return the default display name for a 1-based semester index."""
    if 1 <= semester_idx <= len(SEMESTER_NAMES):
        return SEMESTER_NAMES[semester_idx - 1]
    return f"延毕学期 {semester_idx}"


def course_ids(courses: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return stable string course IDs from a course sequence."""
    return [str(course.get("id")) for course in courses if course.get("id") is not None]


def build_initial_character_state(
    *,
    username: str,
    major_info: Mapping[str, Any],
    course_plan: Mapping[str, Any],
    initial_courses: Sequence[Mapping[str, Any]],
    stat_defaults: Mapping[str, int],
    allocated_stats: Mapping[str, int],
    initial_gold: int,
) -> InitialCharacterState:
    """Build deterministic state fragments for a new character.

    Args:
        username: Prompt-safe display name supplied by the adapter.
        major_info: Normalized major metadata from the active world catalog.
        course_plan: Full major course plan to persist in the save state.
        initial_courses: First-semester course metadata.
        stat_defaults: Runtime stat defaults from the active stat registry.
        allocated_stats: Validated character-creation stat allocations.
        initial_gold: Starting currency from item/economy config.

    Returns:
        State fragments that an adapter can merge with its schema defaults and
        write to storage.
    """
    major_iq_buff = int(major_info.get("iq_buff", 0) or 0)
    allocated_fields: dict[str, Any] = {
        stat_id: value for stat_id, value in allocated_stats.items()
    }
    allocated_fields.update(
        {
            f"initial_{stat_id}": value
            for stat_id, value in allocated_stats.items()
        }
    )
    if "iq" in allocated_stats:
        allocated_fields["iq"] = int(allocated_stats["iq"]) + major_iq_buff

    stats_update: dict[str, Any] = {
        "username": username,
        "elapsed_game_time": 0,
        "major": str(major_info.get("name") or ""),
        "major_abbr": str(major_info.get("abbr") or major_info.get("id") or ""),
        "initial_major_abbr": str(
            major_info.get("abbr") or major_info.get("id") or ""
        ),
        "stress": int(major_info.get("stress_base", 0) or 0),
        "energy": int(stat_defaults.get("energy", 100)),
        "sanity": int(stat_defaults.get("sanity", 100)),
        "gpa": "0.0",
        "highest_gpa": "0.0",
        "gpa_points_total": "0.0",
        "gpa_credits_total": "0.0",
        "reputation": int(stat_defaults.get("reputation", 0)),
        "gold": int(initial_gold),
        "semester": semester_name(1),
        "semester_idx": 1,
        "course_plan_json": json.dumps(course_plan, ensure_ascii=False),
        "course_info_json": json.dumps(list(initial_courses), ensure_ascii=False),
    }
    stats_update.update(allocated_fields)

    ids = course_ids(initial_courses)
    return InitialCharacterState(
        stats_update=stats_update,
        courses_mastery={course_id: 0 for course_id in ids},
        course_states={course_id: 1 for course_id in ids},
        summary={
            "major": stats_update["major"],
            "major_abbr": stats_update["major_abbr"],
            "courses": list(initial_courses),
        },
    )


def build_semester_reset_state(
    *,
    semester_idx: int,
    courses: Sequence[Mapping[str, Any]],
    current_energy: Any,
    energy_default: int,
    energy_minimum: int = 0,
) -> SemesterResetState:
    """Build deterministic state fragments for a new semester."""
    recovered_energy = recover_toward_baseline(
        current_energy,
        baseline=energy_default,
        minimum=energy_minimum,
    )
    term_name = semester_name(semester_idx)
    stats_update: dict[str, Any] = {
        "semester": term_name,
        "elapsed_game_time": 0,
        "exam_completed": 0,
        "energy": recovered_energy,
        "course_info_json": json.dumps(list(courses), ensure_ascii=False),
    }
    ids = course_ids(courses)
    return SemesterResetState(
        stats_update=stats_update,
        courses_mastery={course_id: 0 for course_id in ids},
        course_states={course_id: 1 for course_id in ids},
        summary={
            "semester": term_name,
            "energy_recovery": {
                "before": current_energy,
                "after": recovered_energy,
            },
        },
    )


def achievement_detail(code: Any, item: Any = None) -> AchievementDetail:
    """Normalize one achievement config item into a public detail payload."""
    clean_code = str(code or "").strip()
    data = item if isinstance(item, Mapping) else {}
    return AchievementDetail(
        code=clean_code,
        name=str(data.get("name") or clean_code),
        desc=str(data.get("desc") or data.get("description") or ""),
        icon=str(data.get("icon") or "🏅"),
    )


def achievement_details(
    codes: Sequence[Any],
    config: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Return public achievement details for persisted achievement codes."""
    details: list[dict[str, str]] = []
    normalized_config = {str(key).strip(): value for key, value in config.items()}
    lower_lookup = {key.lower(): key for key in normalized_config}
    for raw_code in codes:
        clean_code = str(raw_code or "").strip()
        config_key = clean_code
        if config_key not in normalized_config:
            config_key = lower_lookup.get(clean_code.lower(), clean_code)
        details.append(
            achievement_detail(
                clean_code,
                normalized_config.get(config_key, {}),
            ).as_dict()
        )
    return details


def normalize_event_entry(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a local/LLM event entry into the adapter-facing shape."""
    return normalize_content_event_entry(raw).as_dict()


def normalize_forum_post(raw: Mapping[str, Any], fallback: str) -> str:
    """Normalize a local forum-library post into visible text content."""
    return normalize_content_forum_post(raw, fallback)
