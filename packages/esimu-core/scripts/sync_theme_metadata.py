"""Generate frontend theme metadata from the active theme manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from esimu_core.authoring import metadata_documents  # noqa: E402
from esimu_core.world.theme_paths import (  # noqa: E402
    active_theme_id,
    frontend_theme_metadata_output,
    project_root,
)

PROJECT_ROOT = project_root()
OUTPUT_PATH = frontend_theme_metadata_output()


def build_typescript() -> str:
    """Render the generated TypeScript theme metadata module."""
    documents = metadata_documents(PROJECT_ROOT, active_theme_id())
    return next(value for path, value in documents.items() if path.name == OUTPUT_PATH.name)


def main() -> int:
    """CLI entry point for writing or checking generated theme metadata."""
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write generated file")
    mode.add_argument("--check", action="store_true", help="check generated file")
    args = parser.parse_args()
    print("NOTE: prefer `esimu sync`; this script is a Beta compatibility wrapper.")

    expected = build_typescript()
    if args.write:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(expected, encoding="utf-8")
        print(f"wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
        return 0

    actual = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
    if actual != expected:
        print(
            f"{OUTPUT_PATH.relative_to(PROJECT_ROOT)} is out of date. "
            "Run: python scripts/sync_theme_metadata.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"{OUTPUT_PATH.relative_to(PROJECT_ROOT)} is up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

