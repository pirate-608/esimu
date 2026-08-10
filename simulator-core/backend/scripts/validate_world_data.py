"""Validate active theme data and checked-in frontend metadata.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

# ruff: noqa: E402, I001

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from esimu_core.world.theme_paths import (
    DEFAULT_THEME_ID,
    active_theme_id,
    lab_root,
)
from esimu_core.world.validation import validate_theme_data
from sync_stat_definitions import OUTPUT_PATH, build_typescript
from sync_story_metadata import (
    OUTPUT_PATH as STORY_OUTPUT_PATH,
    build_typescript as build_story_typescript,
)
from sync_theme_metadata import (
    OUTPUT_PATH as THEME_OUTPUT_PATH,
    build_typescript as build_theme_typescript,
)

LAB_ROOT = lab_root()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(LAB_ROOT))
    except ValueError:
        return str(path)


def _validate_generated_frontend(errors: list[str]) -> None:
    if active_theme_id() != DEFAULT_THEME_ID and not os.environ.get(
        "SIMULATOR_VALIDATE_GENERATED"
    ):
        return

    generated = (
        (OUTPUT_PATH, build_typescript(), "sync_stat_definitions.py"),
        (THEME_OUTPUT_PATH, build_theme_typescript(), "sync_theme_metadata.py"),
        (STORY_OUTPUT_PATH, build_story_typescript(), "sync_story_metadata.py"),
    )
    for output, expected, script_name in generated:
        actual = output.read_text(encoding="utf-8") if output.exists() else ""
        if actual != expected:
            errors.append(
                f"{_relative(output)} is out of date; run "
                f"python scripts/{script_name} --write"
            )


def main() -> int:
    """Validate the active theme plus repository-owned generated metadata."""
    errors = validate_theme_data(LAB_ROOT, active_theme_id())
    _validate_generated_frontend(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"world data validation passed: {active_theme_id()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())