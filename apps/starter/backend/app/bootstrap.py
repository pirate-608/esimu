"""Configure generated-project paths before importing esimu-core loaders."""

from __future__ import annotations

import os
from pathlib import Path


def discover_project_root(start: Path | None = None) -> Path | None:
    """Find the nearest parent that owns a ``themes`` directory."""
    origin = (start or Path(__file__)).resolve()
    for parent in origin.parents:
        if (parent / "themes").is_dir():
            return parent
    return None


def configure_project_environment(default_theme: str = "zju-simplified") -> None:
    """Set path and theme defaults before any eager world loader imports."""
    project_root = discover_project_root()
    if project_root is not None:
        os.environ.setdefault("ESIMU_PROJECT_ROOT", str(project_root))
    os.environ.setdefault("ESIMU_THEME", default_theme)
