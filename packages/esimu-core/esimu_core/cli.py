"""Installed command-line interface for esimu-core.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from esimu_core import __version__


def _theme_from_environment() -> str:
    return (
        os.environ.get("ESIMU_THEME")
        or os.environ.get("SIMULATOR_THEME")
        or "demo-campus"
    )


def _add_validation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="esimu project root; defaults to the current directory",
    )
    parser.add_argument(
        "--theme",
        default=_theme_from_environment(),
        help="theme ID; defaults to ESIMU_THEME or demo-campus",
    )


def build_validation_parser() -> argparse.ArgumentParser:
    """Build the backward-compatible validation parser."""
    parser = argparse.ArgumentParser(
        prog="esimu-validate-world",
        description="Validate one esimu theme pack.",
    )
    _add_validation_arguments(parser)
    return parser


def validate_world(argv: Sequence[str] | None = None) -> int:
    """Set project paths before importing world loaders, then validate."""
    args = build_validation_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    os.environ["ESIMU_PROJECT_ROOT"] = str(root)
    os.environ["ESIMU_THEME"] = args.theme

    from esimu_core.world.validation import validate_theme_data

    errors = validate_theme_data(root, args.theme)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"world data validation passed: {args.theme}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the formal esimu command tree."""
    parser = argparse.ArgumentParser(
        prog="esimu",
        description="Create and validate theme-driven simulator projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    new_parser = subparsers.add_parser("new", help="generate a standalone project")
    new_parser.add_argument("new_args", nargs=argparse.REMAINDER)
    validate_parser = subparsers.add_parser(
        "validate", help="validate a project theme"
    )
    _add_validation_arguments(validate_parser)
    subparsers.add_parser("version", help="print the installed core version")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the formal CLI while preserving the 0.1 module invocation."""
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    if raw_args and raw_args[0].startswith("-"):
        return validate_world(raw_args)

    args = build_parser().parse_args(raw_args)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "validate":
        return validate_world(
            ["--root", str(args.root), "--theme", str(args.theme)]
        )
    if args.command == "new":
        from esimu_core.scaffold import main as scaffold_main

        return scaffold_main(args.new_args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
