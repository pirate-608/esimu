"""Validate gameplay world data and generated stat metadata.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
The checks catch unsupported item/event effect fields and stale generated
frontend stat metadata before those mistakes reach runtime.
"""

# ruff: noqa: E402, I001

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from esimu_core.world.items import ItemCatalog  # noqa: E402
from esimu_core.world.prompts import ThemePrompts  # noqa: E402
from esimu_core.world.stat_definitions import StatDefinitions  # noqa: E402
from esimu_core.world.story import ThemeStory  # noqa: E402
from esimu_core.world.theme import ThemeManifest  # noqa: E402
from esimu_core.world.theme_paths import (  # noqa: E402
    DEFAULT_THEME_ID,
    active_theme_id,
    lab_root,
    theme_dir,
    world_dir,
)
from sync_story_metadata import (  # noqa: E402
    OUTPUT_PATH as STORY_OUTPUT_PATH,
    build_typescript as build_story_typescript,
)
from sync_theme_metadata import (  # noqa: E402
    OUTPUT_PATH as THEME_OUTPUT_PATH,
    build_typescript as build_theme_typescript,
)
from sync_stat_definitions import OUTPUT_PATH, build_typescript  # noqa: E402

LAB_ROOT = lab_root()
WORLD_DIR = world_dir()


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _validate_items(registry: StatDefinitions, errors: list[str]) -> None:
    path = WORLD_DIR / "items.json"
    raw = _load_json(path)
    catalog = ItemCatalog()
    try:
        _, items_by_id = catalog._normalize_config(raw)
    except Exception as exc:
        errors.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
        return
    allowed = registry.item_effect_fields
    for item_id, item in items_by_id.items():
        for field in item.get("effects", {}):
            if field not in allowed:
                errors.append(f"items.{item_id}: unsupported effect field {field}")


def _validate_event_library(registry: StatDefinitions, errors: list[str]) -> None:
    path = WORLD_DIR / "event_library.json"
    if not path.exists():
        return
    raw = _load_json(path)
    if not isinstance(raw, list):
        errors.append(f"{path.relative_to(REPO_ROOT)}: expected a list")
        return
    allowed = registry.event_effect_fields
    for index, event in enumerate(raw):
        options = event.get("options") if isinstance(event, dict) else None
        if not isinstance(options, list):
            errors.append(f"event_library[{index}]: missing options list")
            continue
        for option_index, option in enumerate(options):
            effects = option.get("effects") if isinstance(option, dict) else None
            if not isinstance(effects, dict):
                errors.append(
                    f"event_library[{index}].options[{option_index}]: missing effects"
                )
                continue
            for field in effects:
                if field == "desc":
                    continue
                if field not in allowed:
                    errors.append(
                        f"event_library[{index}].options[{option_index}]: "
                        f"unsupported effect field {field}"
                    )


def _validate_generated_frontend(errors: list[str]) -> None:
    if active_theme_id() != DEFAULT_THEME_ID and not os.environ.get(
        "SIMULATOR_VALIDATE_GENERATED"
    ):
        return

    expected = build_typescript()
    actual = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
    if actual != expected:
        errors.append(
            f"{OUTPUT_PATH.relative_to(LAB_ROOT)} is out of date; run "
            "python scripts/sync_stat_definitions.py --write"
        )

    expected_theme = build_theme_typescript()
    actual_theme = (
        THEME_OUTPUT_PATH.read_text(encoding="utf-8")
        if THEME_OUTPUT_PATH.exists()
        else ""
    )
    if actual_theme != expected_theme:
        errors.append(
            f"{THEME_OUTPUT_PATH.relative_to(LAB_ROOT)} is out of date; run "
            "python scripts/sync_theme_metadata.py --write"
        )

    expected_story = build_story_typescript()
    actual_story = (
        STORY_OUTPUT_PATH.read_text(encoding="utf-8")
        if STORY_OUTPUT_PATH.exists()
        else ""
    )
    if actual_story != expected_story:
        errors.append(
            f"{STORY_OUTPUT_PATH.relative_to(LAB_ROOT)} is out of date; run "
            "python scripts/sync_story_metadata.py --write"
        )


def _validate_story_assets(errors: list[str]) -> None:
    story = ThemeStory().config
    public_images_dir = (
        LAB_ROOT
        / "apps"
        / "zju-reference"
        / "zjus-frontend"
        / "public"
        / "images"
    )
    theme_assets_dir = theme_dir() / "assets"
    image_names = {
        scene.image for scene in story.prologue.scenes
    } | set(story.endings.graduation_background_images)

    for image_name in sorted(image_names):
        public_path = public_images_dir / image_name
        theme_path = theme_assets_dir / image_name
        if not public_path.exists() and not theme_path.exists():
            errors.append(
                f"story asset {image_name} not found in "
                f"{public_images_dir.relative_to(LAB_ROOT)} or "
                f"{theme_assets_dir.relative_to(LAB_ROOT)}"
            )


def main() -> int:
    """CLI entry point for validating registry, item, and event world data."""
    errors: list[str] = []
    try:
        registry = StatDefinitions(WORLD_DIR / "stat_definitions.json")
    except Exception as exc:
        print(f"stat_definitions.json: {exc}", file=sys.stderr)
        return 1

    try:
        ThemeManifest()
    except Exception as exc:
        print(f"theme.json: {exc}", file=sys.stderr)
        return 1

    try:
        ThemeStory()
    except Exception as exc:
        print(f"story.json: {exc}", file=sys.stderr)
        return 1

    try:
        ThemePrompts()
    except Exception as exc:
        print(f"prompts.json: {exc}", file=sys.stderr)
        return 1

    for filename in ("game_balance.json", "items.json"):
        try:
            _load_json(WORLD_DIR / filename)
        except Exception as exc:
            errors.append(f"{WORLD_DIR / filename}: {exc}")

    _validate_items(registry, errors)
    _validate_event_library(registry, errors)
    _validate_story_assets(errors)
    _validate_generated_frontend(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("world data validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

