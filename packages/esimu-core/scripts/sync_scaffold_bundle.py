"""Build the deterministic Starter bundle shipped in esimu-core wheels."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys
import zipfile

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
OUTPUT = PACKAGE_ROOT / "esimu_core" / "scaffold" / "esimu-starter.zip"
SOURCES = (
    PROJECT_ROOT / "apps" / "starter",
    PROJECT_ROOT / "themes" / "zju-simplified",
    PROJECT_ROOT / "themes" / "demo-campus",
    PROJECT_ROOT / "templates" / "agent" / "AGENTS.md",
    PACKAGE_ROOT / "scripts" / "scaffold_game_stat.py",
    PACKAGE_ROOT / "scripts" / "scaffold_world_data.py",
)
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    ".vite",
    "data",
}
TEXT_SUFFIXES = {
    ".css",
    ".example",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}
ARCHIVE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def _archive_name(path: Path) -> str:
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    raise ValueError(f"bundle source escaped project root: {path}")


def build_bundle() -> bytes:
    """Return a reproducible zip containing canonical Starter inputs."""
    buffer = BytesIO()
    files: list[Path] = []
    for source in SOURCES:
        if source.is_dir():
            files.extend(path for path in source.rglob("*") if path.is_file())
        else:
            files.append(source)

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in sorted(files, key=_archive_name):
            relative = path.relative_to(PROJECT_ROOT)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            info = zipfile.ZipInfo(_archive_name(path), ARCHIVE_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            payload = path.read_bytes()
            if path.suffix.lower() in TEXT_SUFFIXES:
                payload = payload.replace(b"\r\n", b"\n")
            archive.writestr(info, payload)
    return buffer.getvalue()


def main(argv: list[str] | None = None) -> int:
    """Write or check the wheel-owned scaffold bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    expected = build_bundle()
    actual = OUTPUT.read_bytes() if OUTPUT.exists() else b""
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(expected)
        print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
        return 0
    if actual != expected:
        print(
            "ERROR: scaffold bundle is stale; run "
            "python packages/esimu-core/scripts/sync_scaffold_bundle.py --write",
            file=sys.stderr,
        )
        return 1
    print("scaffold bundle is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
