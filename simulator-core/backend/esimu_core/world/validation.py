"""Standalone validation for an esimu theme pack.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from esimu_core.world.items import ItemCatalog
from esimu_core.world.prompts import ThemePrompts
from esimu_core.world.stat_definitions import StatDefinitions
from esimu_core.world.story import ThemeStory
from esimu_core.world.theme import ThemeManifest
from esimu_core.world.theme_contract import validate_theme_pack
from esimu_core.world.theme_paths import active_theme_id, lab_root


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _validate_items(
    world: Path,
    registry: StatDefinitions,
    errors: list[str],
) -> None:
    path = world / "items.json"
    try:
        raw = _load_json(path)
        _, items_by_id = ItemCatalog()._normalize_config(raw)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return

    allowed = registry.item_effect_fields
    for item_id, item in items_by_id.items():
        for field in item.get("effects", {}):
            if field not in allowed:
                errors.append(f"items.{item_id}: unsupported effect field {field}")


def _validate_event_library(
    world: Path,
    registry: StatDefinitions,
    errors: list[str],
) -> None:
    path = world / "event_library.json"
    if not path.exists():
        return
    raw = _load_json(path)
    if not isinstance(raw, list):
        errors.append(f"{path}: expected a list")
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
                if field != "desc" and field not in allowed:
                    errors.append(
                        f"event_library[{index}].options[{option_index}]: "
                        f"unsupported effect field {field}"
                    )


def validate_theme_data(root: str | Path, theme_id: str) -> list[str]:
    """Return validation errors for one project-local theme pack."""
    project_root = Path(root).expanduser().resolve()
    theme = project_root / "themes" / theme_id
    world = theme / "world"
    errors = [issue.format() for issue in validate_theme_pack(theme)]

    try:
        registry = StatDefinitions(world / "stat_definitions.json")
    except Exception as exc:
        errors.append(f"stat_definitions.json: {exc}")
        return errors

    try:
        ThemeManifest(theme / "theme.json")
    except Exception as exc:
        errors.append(f"theme.json: {exc}")

    try:
        story = ThemeStory(theme / "story.json")
    except Exception as exc:
        errors.append(f"story.json: {exc}")
        story = None

    try:
        ThemePrompts(theme / "prompts.json")
    except Exception as exc:
        errors.append(f"prompts.json: {exc}")

    for filename in ("game_balance.json", "items.json"):
        path = world / filename
        try:
            _load_json(path)
        except Exception as exc:
            errors.append(f"{_display_path(path, project_root)}: {exc}")

    _validate_items(world, registry, errors)
    _validate_event_library(world, registry, errors)

    if story is not None:
        image_names = {
            scene.image for scene in story.config.prologue.scenes
        } | set(story.config.endings.graduation_background_images)
        assets = theme / "assets"
        for image_name in sorted(image_names):
            if not (assets / image_name).exists():
                errors.append(
                    f"story asset {image_name} not found in "
                    f"{_display_path(assets, project_root)}"
                )

    return errors


def build_parser() -> argparse.ArgumentParser:
    """Build the installed validation command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="simulator project root; defaults to SIMULATOR_LAB_ROOT or discovery",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="theme ID; defaults to SIMULATOR_THEME",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate one theme and return a process exit code."""
    args = build_parser().parse_args(argv)
    root = args.root or lab_root()
    theme_id = args.theme or active_theme_id()
    errors = validate_theme_data(root, theme_id)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"world data validation passed: {theme_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())