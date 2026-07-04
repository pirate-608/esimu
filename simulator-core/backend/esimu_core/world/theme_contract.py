"""Schema-equivalent validation for esimu theme packs.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The contract validator is intentionally stricter than runtime loaders. Runtime
loaders should stay tolerant where possible; this module is the authoring-time
gate that tells theme maintainers which files or fields need attention before
the app starts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from esimu_core.world.prompts import PromptConfig
from esimu_core.world.stat_definitions import StatDefinitionsConfig
from esimu_core.world.story import StoryConfig
from esimu_core.world.theme import ThemeManifestConfig
from esimu_core.world.theme_paths import theme_dir

REQUIRED_THEME_FILES = (
    "theme.json",
    "story.json",
    "prompts.json",
)

REQUIRED_WORLD_FILES = (
    "stat_definitions.json",
    "game_balance.json",
    "items.json",
    "majors.json",
    "achievements.json",
    "event_library.json",
    "cc98_library.json",
    "characters.json",
    "graduation_comments.json",
)


@dataclass(frozen=True)
class ContractIssue:
    """One author-facing theme contract validation issue."""

    path: str
    message: str

    def format(self) -> str:
        """Return a stable CLI-friendly issue string."""
        return f"{self.path}: {self.message}"


def validate_active_theme_contract() -> list[ContractIssue]:
    """Validate the currently selected theme pack."""
    return validate_theme_pack(theme_dir())


def validate_theme_pack(theme_path: str | Path) -> list[ContractIssue]:
    """Validate the file and shape contract for one theme pack."""
    root = Path(theme_path)
    world = root / "world"
    issues: list[ContractIssue] = []

    if not root.exists():
        return [ContractIssue(str(root), "theme directory does not exist")]
    if not world.exists():
        issues.append(_issue(root, "world", "world directory is required"))

    for relative in REQUIRED_THEME_FILES:
        _require_file(root, relative, issues)
    for relative in REQUIRED_WORLD_FILES:
        _require_file(world, relative, issues)
    if not (world / "courses").is_dir():
        issues.append(_issue(world, "courses", "courses directory is required"))

    theme_raw = _load_json(root, "theme.json", issues)
    if isinstance(theme_raw, Mapping):
        _validate_model(root, "theme.json", ThemeManifestConfig, theme_raw, issues)

    story_raw = _load_json(root, "story.json", issues)
    if isinstance(story_raw, Mapping):
        _validate_model(root, "story.json", StoryConfig, story_raw, issues)

    prompts_raw = _load_json(root, "prompts.json", issues)
    if isinstance(prompts_raw, Mapping):
        _validate_model(root, "prompts.json", PromptConfig, prompts_raw, issues)

    stats_raw = _load_json(world, "stat_definitions.json", issues)
    if isinstance(stats_raw, Mapping):
        _validate_model(
            world,
            "stat_definitions.json",
            StatDefinitionsConfig,
            stats_raw,
            issues,
        )

    _validate_balance(world, issues)
    _validate_items(world, issues)
    major_ids = _validate_majors(world, issues)
    _validate_courses(world, major_ids, issues)
    _validate_achievements(world, issues)
    _validate_event_library(world, issues)
    _validate_forum_library(world, issues)
    _validate_characters(world, issues)
    _validate_graduation_comments(world, issues)
    return issues


def assert_valid_theme_pack(theme_path: str | Path) -> None:
    """Raise ValueError when a theme pack violates the contract."""
    issues = validate_theme_pack(theme_path)
    if issues:
        joined = "\n".join(issue.format() for issue in issues)
        raise ValueError(f"theme pack contract failed:\n{joined}")


def _validate_balance(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "game_balance.json", issues)
    if not isinstance(raw, Mapping):
        return
    tick = _object(raw.get("tick"))
    events = _object(raw.get("events"))
    game_over = _object(raw.get("game_over"))
    if not tick:
        issues.append(_issue(world, "game_balance.json", "tick object is required"))
    else:
        _require_number(world, "game_balance.json", tick, "interval_seconds", issues)
    if not isinstance(events.get("random_event"), Mapping):
        issues.append(
            _issue(world, "game_balance.json", "events.random_event object is required")
        )
    if not isinstance(events.get("dingtalk"), Mapping):
        issues.append(
            _issue(world, "game_balance.json", "events.dingtalk object is required")
        )
    if not game_over:
        issues.append(
            _issue(world, "game_balance.json", "game_over object is required")
        )


def _validate_items(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "items.json", issues)
    if not isinstance(raw, Mapping):
        return
    if not isinstance(raw.get("economy"), Mapping):
        issues.append(_issue(world, "items.json", "economy object is required"))
    items = raw.get("items")
    if not isinstance(items, list):
        issues.append(_issue(world, "items.json", "items array is required"))
        return
    seen: set[str] = set()
    for index, item in enumerate(items):
        location = f"items[{index}]"
        if not isinstance(item, Mapping):
            issues.append(_issue(world, "items.json", f"{location} must be an object"))
            continue
        item_id = _string(item.get("id"))
        if not item_id:
            issues.append(_issue(world, "items.json", f"{location}.id is required"))
        elif item_id in seen:
            issues.append(_issue(world, "items.json", f"duplicate item id {item_id}"))
        seen.add(item_id)
        _require_string(world, "items.json", item, "name", issues, prefix=location)
        _require_number(world, "items.json", item, "price", issues, prefix=location)
        effects = item.get("effects")
        if effects is not None and not isinstance(effects, Mapping):
            issues.append(
                _issue(world, "items.json", f"{location}.effects must be an object")
            )


def _validate_majors(world: Path, issues: list[ContractIssue]) -> list[str]:
    raw = _load_json(world, "majors.json", issues)
    majors = _major_entries(raw)
    if not majors:
        issues.append(_issue(world, "majors.json", "at least one major is required"))
        return []

    seen: set[str] = set()
    major_ids: list[str] = []
    for index, major in enumerate(majors):
        location = f"majors[{index}]"
        major_id = _string(major.get("abbr") or major.get("id"))
        if not major_id:
            issues.append(
                _issue(world, "majors.json", f"{location}.abbr or id is required")
            )
            continue
        if major_id in seen:
            issues.append(_issue(world, "majors.json", f"duplicate major {major_id}"))
        seen.add(major_id)
        major_ids.append(major_id)
        _require_string(world, "majors.json", major, "name", issues, prefix=location)
    return major_ids


def _validate_courses(
    world: Path,
    major_ids: Iterable[str],
    issues: list[ContractIssue],
) -> None:
    courses_dir = world / "courses"
    for major_id in major_ids:
        filename = f"{major_id}.json"
        raw = _load_json(courses_dir, filename, issues)
        if raw is None:
            continue
        terms = _course_terms(raw)
        if not terms:
            issues.append(
                _issue(courses_dir, filename, "course plan must contain courses")
            )
            continue
        for term_index, courses in enumerate(terms):
            if not courses:
                issues.append(
                    _issue(
                        courses_dir,
                        filename,
                        f"term {term_index + 1} must contain at least one course",
                    )
                )
            for course_index, course in enumerate(courses):
                location = f"terms[{term_index}].courses[{course_index}]"
                if not isinstance(course, Mapping):
                    issues.append(
                        _issue(courses_dir, filename, f"{location} must be an object")
                    )
                    continue
                _require_string(courses_dir, filename, course, "id", issues, prefix=location)
                _require_string(courses_dir, filename, course, "name", issues, prefix=location)
                _require_number(
                    courses_dir,
                    filename,
                    course,
                    "credits",
                    issues,
                    prefix=location,
                    minimum=0,
                    exclusive_minimum=True,
                )


def _validate_achievements(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "achievements.json", issues)
    entries = _achievement_entries(raw)
    if not entries:
        issues.append(
            _issue(world, "achievements.json", "at least one achievement is required")
        )
        return
    seen: set[str] = set()
    for index, (code, achievement) in enumerate(entries):
        location = f"achievements[{index}]"
        if not code:
            issues.append(
                _issue(world, "achievements.json", f"{location}.code is required")
            )
            continue
        if code in seen:
            issues.append(
                _issue(world, "achievements.json", f"duplicate achievement {code}")
            )
        seen.add(code)
        _require_string(
            world,
            "achievements.json",
            achievement,
            "name",
            issues,
            prefix=location,
        )
        if not _string(achievement.get("desc") or achievement.get("description")):
            issues.append(
                _issue(
                    world,
                    "achievements.json",
                    f"{location}.desc or description is required",
                )
            )


def _validate_event_library(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "event_library.json", issues)
    if not isinstance(raw, list):
        issues.append(_issue(world, "event_library.json", "expected an array"))
        return
    if not raw:
        issues.append(
            _issue(world, "event_library.json", "at least one event is required")
        )
    for index, event in enumerate(raw):
        location = f"events[{index}]"
        if not isinstance(event, Mapping):
            issues.append(
                _issue(world, "event_library.json", f"{location} must be an object")
            )
            continue
        _require_string(world, "event_library.json", event, "title", issues, prefix=location)
        if not _string(event.get("desc") or event.get("description")):
            issues.append(
                _issue(
                    world,
                    "event_library.json",
                    f"{location}.desc or description is required",
                )
            )
        options = event.get("options")
        if not isinstance(options, list) or not options:
            issues.append(
                _issue(
                    world,
                    "event_library.json",
                    f"{location}.options must be a non-empty array",
                )
            )
            continue
        for option_index, option in enumerate(options):
            option_loc = f"{location}.options[{option_index}]"
            if not isinstance(option, Mapping):
                issues.append(
                    _issue(
                        world,
                        "event_library.json",
                        f"{option_loc} must be an object",
                    )
                )
                continue
            _require_string(
                world,
                "event_library.json",
                option,
                "text",
                issues,
                prefix=option_loc,
            )
            if not isinstance(option.get("effects"), Mapping):
                issues.append(
                    _issue(
                        world,
                        "event_library.json",
                        f"{option_loc}.effects object is required",
                    )
                )


def _validate_forum_library(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "cc98_library.json", issues)
    if not isinstance(raw, list):
        issues.append(_issue(world, "cc98_library.json", "expected an array"))
        return
    if not raw:
        issues.append(
            _issue(world, "cc98_library.json", "at least one forum post is required")
        )
    for index, post in enumerate(raw):
        if not isinstance(post, Mapping):
            issues.append(
                _issue(world, "cc98_library.json", f"posts[{index}] must be an object")
            )
            continue
        _require_string(
            world,
            "cc98_library.json",
            post,
            "content",
            issues,
            prefix=f"posts[{index}]",
        )


def _validate_characters(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "characters.json", issues)
    if not isinstance(raw, list):
        issues.append(_issue(world, "characters.json", "expected an array"))
        return
    if not raw:
        issues.append(
            _issue(world, "characters.json", "at least one character is required")
        )
    for index, character in enumerate(raw):
        location = f"characters[{index}]"
        if not isinstance(character, Mapping):
            issues.append(
                _issue(world, "characters.json", f"{location} must be an object")
            )
            continue
        _require_string(world, "characters.json", character, "name", issues, prefix=location)
        _require_string(world, "characters.json", character, "role", issues, prefix=location)
        if not _string(character.get("content") or character.get("description")):
            issues.append(
                _issue(
                    world,
                    "characters.json",
                    f"{location}.content or description is required",
                )
            )


def _validate_graduation_comments(world: Path, issues: list[ContractIssue]) -> None:
    raw = _load_json(world, "graduation_comments.json", issues)
    if not isinstance(raw, Mapping):
        issues.append(
            _issue(world, "graduation_comments.json", "expected an object")
        )
        return
    comments = raw.get("comments")
    if not isinstance(comments, list) or not comments:
        issues.append(
            _issue(
                world,
                "graduation_comments.json",
                "comments must be a non-empty array",
            )
        )
        return
    for index, comment in enumerate(comments):
        location = f"comments[{index}]"
        if not isinstance(comment, Mapping):
            issues.append(
                _issue(
                    world,
                    "graduation_comments.json",
                    f"{location} must be an object",
                )
            )
            continue
        has_texts = isinstance(comment.get("texts"), list) and comment.get("texts")
        has_paragraphs = (
            isinstance(comment.get("paragraphs"), list) and comment.get("paragraphs")
        )
        if not has_texts and not has_paragraphs:
            issues.append(
                _issue(
                    world,
                    "graduation_comments.json",
                    f"{location}.texts or paragraphs is required",
                )
            )


def _load_json(root: Path, relative: str, issues: list[ContractIssue]) -> Any:
    path = root / relative
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(_issue(root, relative, f"invalid JSON: {exc}"))
        return None


def _require_file(root: Path, relative: str, issues: list[ContractIssue]) -> None:
    if not (root / relative).is_file():
        issues.append(_issue(root, relative, "required file is missing"))


def _validate_model(
    root: Path,
    relative: str,
    model: Any,
    raw: Mapping[str, Any],
    issues: list[ContractIssue],
) -> None:
    try:
        model.model_validate(raw)
    except Exception as exc:
        issues.append(_issue(root, relative, str(exc)))


def _major_entries(raw: Any) -> list[Mapping[str, Any]]:
    if isinstance(raw, list):
        return [major for major in raw if isinstance(major, Mapping)]
    if isinstance(raw, Mapping):
        return [
            major
            for group in raw.values()
            if isinstance(group, list)
            for major in group
            if isinstance(major, Mapping)
        ]
    return []


def _course_terms(raw: Any) -> list[list[Any]]:
    if isinstance(raw, list):
        return [raw]
    if not isinstance(raw, Mapping):
        return []
    terms = raw.get("semesters") or raw.get("plan") or []
    if not isinstance(terms, list):
        return []
    return [
        term.get("courses")
        for term in terms
        if isinstance(term, Mapping) and isinstance(term.get("courses"), list)
    ]


def _achievement_entries(raw: Any) -> list[tuple[str, Mapping[str, Any]]]:
    if isinstance(raw, Mapping):
        return [
            (str(code).strip(), item)
            for code, item in raw.items()
            if isinstance(item, Mapping)
        ]
    if isinstance(raw, list):
        return [
            (str(item.get("code") or item.get("id") or "").strip(), item)
            for item in raw
            if isinstance(item, Mapping)
        ]
    return []


def _require_string(
    root: Path,
    relative: str,
    data: Mapping[str, Any],
    field: str,
    issues: list[ContractIssue],
    *,
    prefix: str = "",
) -> None:
    if not _string(data.get(field)):
        location = f"{prefix}.{field}" if prefix else field
        issues.append(_issue(root, relative, f"{location} is required"))


def _require_number(
    root: Path,
    relative: str,
    data: Mapping[str, Any],
    field: str,
    issues: list[ContractIssue],
    *,
    prefix: str = "",
    minimum: float | None = None,
    exclusive_minimum: bool = False,
) -> None:
    value = data.get(field)
    location = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, int | float):
        issues.append(_issue(root, relative, f"{location} must be numeric"))
        return
    if minimum is None:
        return
    if exclusive_minimum and value <= minimum:
        issues.append(_issue(root, relative, f"{location} must be > {minimum}"))
    elif not exclusive_minimum and value < minimum:
        issues.append(_issue(root, relative, f"{location} must be >= {minimum}"))


def _object(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _issue(root: Path, relative: str, message: str) -> ContractIssue:
    return ContractIssue(path=str(root / relative), message=message)
