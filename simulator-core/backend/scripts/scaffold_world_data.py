"""Draft small world-data entries for an esimu theme.

The helpers favor reviewable snippets over automatic broad rewrites. Use them
to start an item, achievement, event, course, or prompt fragment, then run the
theme validator before committing the result.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from esimu_core.world.theme_paths import theme_dir, world_file  # noqa: E402


def _id(value: str) -> str:
    candidate = value.strip()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", candidate):
        raise ValueError("id must match [a-z][a-z0-9_]*")
    return candidate


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_unique_list(path: Path, entry: dict[str, Any], *, id_field: str) -> None:
    data = _load_json(path, [])
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    entry_id = entry[id_field]
    if any(isinstance(item, dict) and item.get(id_field) == entry_id for item in data):
        raise ValueError(f"{entry_id} already exists in {path.name}")
    data.append(entry)
    _write_json(path, data)
    print(f"added {entry_id} to {path}")


def scaffold_item(args: argparse.Namespace) -> int:
    """Draft or append an item catalog entry."""
    entry = {
        "id": _id(args.item_id),
        "name": args.name or args.item_id,
        "category": args.category,
        "tags": [tag.strip() for tag in args.tags.split(",") if tag.strip()],
        "price": args.price,
        "description": args.description or "Describe what this item does.",
        "effects": {args.effect: args.effect_value},
    }
    if args.sell_price is not None:
        entry["sell_price"] = args.sell_price
    if args.write:
        path = world_file("items.json")
        data = _load_json(path, {"version": "1.0.0", "economy": {}, "items": []})
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise ValueError("items.json must contain an items array")
        if any(item.get("id") == entry["id"] for item in data["items"] if isinstance(item, dict)):
            raise ValueError(f"item already exists: {entry['id']}")
        data["items"].append(entry)
        _write_json(path, data)
        print(f"added {entry['id']} to {path}")
    else:
        _print_json(entry)
    return 0


def scaffold_achievement(args: argparse.Namespace) -> int:
    """Draft or append an achievement entry."""
    entry = {
        "id": _id(args.achievement_id),
        "name": args.name or args.achievement_id,
        "description": args.description or "Describe how the player unlocks this.",
        "icon": args.icon,
    }
    if args.write:
        _append_unique_list(world_file("achievements.json"), entry, id_field="id")
    else:
        _print_json(entry)
    return 0


def scaffold_event(args: argparse.Namespace) -> int:
    """Draft or append a local event-library entry."""
    entry = {
        "id": _id(args.event_id),
        "title": args.title or args.event_id,
        "description": args.description or "A short event setup.",
        "options": [
            {
                "text": args.option_text,
                "effects": {
                    args.effect: args.effect_value,
                    "desc": "Describe what changed.",
                },
            }
        ],
    }
    if args.write:
        _append_unique_list(world_file("event_library.json"), entry, id_field="id")
    else:
        _print_json(entry)
    return 0


def scaffold_course(args: argparse.Namespace) -> int:
    """Draft one course entry for a major/role course plan."""
    entry = {
        "id": _id(args.course_id),
        "name": args.name or args.course_id,
        "credits": args.credits,
        "difficulty": args.difficulty,
        "description": args.description or "Course or task description.",
    }
    if args.write:
        path = world_file(f"courses/{args.plan}.json")
        data = _load_json(path, [])
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON list")
        if any(item.get("id") == entry["id"] for item in data if isinstance(item, dict)):
            raise ValueError(f"course already exists: {entry['id']}")
        data.append(entry)
        _write_json(path, data)
        print(f"added {entry['id']} to {path}")
    else:
        _print_json(entry)
    return 0


def scaffold_prompt(args: argparse.Namespace) -> int:
    """Draft or update one prompt fragment."""
    path = theme_dir() / "prompts.json"
    if args.write:
        data = _load_json(path, {})
        if not isinstance(data, dict):
            raise ValueError("prompts.json must be an object")
        data[args.key] = args.text
        _write_json(path, data)
        print(f"set prompts.{args.key} in {path}")
    else:
        _print_json({args.key: args.text})
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the world-data scaffold parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    item = subparsers.add_parser("item", help="draft an item entry")
    item.add_argument("item_id")
    item.add_argument("--name", default="")
    item.add_argument("--category", default="general")
    item.add_argument("--tags", default="通用")
    item.add_argument("--price", type=int, default=50)
    item.add_argument("--sell-price", type=int)
    item.add_argument("--description", default="")
    item.add_argument("--effect", default="energy")
    item.add_argument("--effect-value", type=int, default=5)
    item.add_argument("--write", action="store_true")
    item.set_defaults(func=scaffold_item)

    achievement = subparsers.add_parser("achievement", help="draft an achievement")
    achievement.add_argument("achievement_id")
    achievement.add_argument("--name", default="")
    achievement.add_argument("--description", default="")
    achievement.add_argument("--icon", default="🏅")
    achievement.add_argument("--write", action="store_true")
    achievement.set_defaults(func=scaffold_achievement)

    event = subparsers.add_parser("event", help="draft a local event")
    event.add_argument("event_id")
    event.add_argument("--title", default="")
    event.add_argument("--description", default="")
    event.add_argument("--option-text", default="试试看")
    event.add_argument("--effect", default="sanity")
    event.add_argument("--effect-value", type=int, default=5)
    event.add_argument("--write", action="store_true")
    event.set_defaults(func=scaffold_event)

    course = subparsers.add_parser("course", help="draft a course/task entry")
    course.add_argument("course_id")
    course.add_argument("--plan", default="GEN")
    course.add_argument("--name", default="")
    course.add_argument("--credits", type=float, default=3)
    course.add_argument("--difficulty", type=float, default=1)
    course.add_argument("--description", default="")
    course.add_argument("--write", action="store_true")
    course.set_defaults(func=scaffold_course)

    prompt = subparsers.add_parser("prompt", help="draft or set a prompt fragment")
    prompt.add_argument("key")
    prompt.add_argument("--text", default="Describe this prompt fragment.")
    prompt.add_argument("--write", action="store_true")
    prompt.set_defaults(func=scaffold_prompt)
    return parser


def main() -> int:
    """CLI entry point."""
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
