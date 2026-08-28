"""Installed command-line interface for esimu-core.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Sequence

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


def _add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
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
    sync_parser = subparsers.add_parser(
        "sync", help="check or write generated frontend metadata"
    )
    _add_validation_arguments(sync_parser)
    sync_parser.add_argument("--write", action="store_true")
    doctor_parser = subparsers.add_parser(
        "doctor", help="diagnose a project, theme, and local toolchain"
    )
    _add_validation_arguments(doctor_parser)
    _add_json_argument(doctor_parser)
    inspect_parser = subparsers.add_parser(
        "inspect", help="summarize a project and active theme"
    )
    _add_validation_arguments(inspect_parser)
    _add_json_argument(inspect_parser)
    _add_authoring_parsers(subparsers)
    subparsers.add_parser("version", help="print the installed core version")
    return parser


def _add_authoring_parsers(subparsers: Any) -> None:
    add_parser = subparsers.add_parser("add", help="preview or add theme content")
    kinds = add_parser.add_subparsers(dest="entry_kind", required=True)

    def entry_parser(kind: str, help_text: str) -> argparse.ArgumentParser:
        parser = kinds.add_parser(kind, help=help_text)
        parser.add_argument("entry_id")
        _add_validation_arguments(parser)
        parser.add_argument("--write", action="store_true")
        return parser

    stat = entry_parser("stat", "add a stat definition")
    stat.add_argument("--label", default="")
    stat.add_argument("--icon", default="")
    stat.add_argument("--default", type=int, default=0)
    stat.add_argument("--minimum", type=int, default=0)
    stat.add_argument("--maximum", type=int, default=200)
    stat.add_argument(
        "--positive-endpoint", choices=["max", "min", "none"], default="max"
    )
    stat.add_argument("--allocatable", action="store_true")
    stat.add_argument(
        "--adjust-budget",
        action="store_true",
        help="increase initial_budget by the new allocatable stat default",
    )
    stat.add_argument("--allow-item-effect", action="store_true")
    stat.add_argument("--allow-event-effect", action="store_true")
    stat.add_argument("--llm-context", action="store_true")
    stat.add_argument("--show-in-hud", action="store_true")

    item = entry_parser("item", "add an item definition")
    item.add_argument("--name", default="")
    item.add_argument("--category", default="general")
    item.add_argument("--tags", default="general")
    item.add_argument("--price", type=int, default=50)
    item.add_argument("--sell-price", type=int)
    item.add_argument("--description", default="")
    item.add_argument("--effect", default="energy")
    item.add_argument("--effect-value", type=int, default=5)

    achievement = entry_parser("achievement", "add a declarative achievement")
    achievement.add_argument("--name", default="")
    achievement.add_argument("--description", default="")
    achievement.add_argument("--icon", default="🏅")
    achievement.add_argument(
        "--scope", choices=["stat", "action", "session"], default="action"
    )
    achievement.add_argument("--key", default="relax")
    achievement.add_argument(
        "--op", choices=["gte", "gt", "lte", "lt", "eq"], default="gte"
    )
    achievement.add_argument("--value", default="1")

    event = entry_parser("event", "add a local event")
    event.add_argument("--title", default="")
    event.add_argument("--description", default="")
    event.add_argument("--option-text", default="Try it")
    event.add_argument("--second-option-text", default="Leave it")
    event.add_argument("--result", default="")
    event.add_argument("--second-result", default="You let it pass.")
    event.add_argument("--effect", default="sanity")
    event.add_argument("--effect-value", type=int, default=5)

    course = entry_parser("course", "add a course or task")
    course.add_argument("--plan", default="GEN")
    course.add_argument("--name", default="")
    course.add_argument("--credits", type=float, default=3)
    course.add_argument("--difficulty", type=float, default=1)
    course.add_argument("--semester", type=int, default=1)
    course.add_argument("--description", default="")

    prompt = entry_parser("prompt", "add a prompt fragment")
    prompt.add_argument("--text", default="Describe this prompt fragment.")


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
    if args.command in {"sync", "doctor", "inspect", "add"}:
        return _run_authoring_command(args)
    raise RuntimeError(f"unsupported command: {args.command}")


def _run_authoring_command(args: argparse.Namespace) -> int:
    from esimu_core.authoring import (
        add_world_entry,
        doctor_project,
        inspect_project,
        sync_project_metadata,
    )

    try:
        if args.command == "sync":
            result = sync_project_metadata(args.root, args.theme, write=args.write)
            if args.write:
                print("frontend metadata written and theme validation passed")
                return 0
            if not result["current"]:
                print("ERROR: generated metadata is stale: " + ", ".join(result["stale"]), file=sys.stderr)
                return 1
            print("frontend metadata is current")
            return 0
        if args.command == "doctor":
            result = doctor_project(args.root, args.theme)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for check in result["checks"]:
                    print(f"[{check['status'].upper()}] {check['name']}: {check['detail']}")
            return 0 if result["ok"] else 1
        if args.command == "inspect":
            result = inspect_project(args.root, args.theme)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"theme: {result['theme']['displayName']} ({args.theme})")
                print(
                    "contracts: "
                    + ", ".join(
                        f"{key}=v{value}" for key, value in result["contracts"].items()
                    )
                )
                for key, value in result["counts"].items():
                    print(f"{key}: {value}")
            return 0
        options = vars(args).copy()
        result = add_world_entry(
            args.root,
            args.theme,
            args.entry_kind,
            args.entry_id,
            options,
            write=args.write,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not args.write:
            print("dry run only; add --write to update the theme")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
