"""Installed command-line entry points for esimu-core.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence


def build_validation_parser() -> argparse.ArgumentParser:
    """Build the project-local theme validation parser."""
    parser = argparse.ArgumentParser(
        prog="esimu-validate-world",
        description="Validate one esimu theme pack.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="simulator project root; defaults to the current directory",
    )
    parser.add_argument(
        "--theme",
        default=os.environ.get("SIMULATOR_THEME", "demo-campus"),
        help="theme ID; defaults to SIMULATOR_THEME or demo-campus",
    )
    return parser


def validate_world(argv: Sequence[str] | None = None) -> int:
    """Set project paths before importing world loaders, then validate."""
    args = build_validation_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    os.environ["SIMULATOR_LAB_ROOT"] = str(root)
    os.environ["SIMULATOR_THEME"] = args.theme

    from esimu_core.world.validation import validate_theme_data

    errors = validate_theme_data(root, args.theme)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"world data validation passed: {args.theme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_world())