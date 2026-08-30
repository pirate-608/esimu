"""Theme and world-data path resolution for esimu projects."""

from __future__ import annotations

import os
from pathlib import Path
import warnings

DEFAULT_THEME_ID = "zju-simplified"


def _environment_value(primary: str, legacy: str) -> str | None:
    """Read a formal environment variable with one-beta legacy support."""
    value = os.environ.get(primary)
    if value is not None:
        return value
    value = os.environ.get(legacy)
    if value is not None:
        warnings.warn(
            f"{legacy} is deprecated; use {primary}",
            DeprecationWarning,
            stacklevel=3,
        )
    return value


def project_root() -> Path:
    """Return the active esimu project root directory."""
    explicit = _environment_value("ESIMU_PROJECT_ROOT", "SIMULATOR_LAB_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()

    for parent in Path(__file__).resolve().parents:
        if (parent / "themes").is_dir():
            return parent

    return Path.cwd()


def lab_root() -> Path:
    """Return the project root through the deprecated 0.1 API alias."""
    warnings.warn(
        "lab_root() is deprecated; use project_root()",
        DeprecationWarning,
        stacklevel=2,
    )
    return project_root()


def active_theme_id() -> str:
    """Return the selected theme ID, defaulting to the neutral demo theme."""
    value = _environment_value("ESIMU_THEME", "SIMULATOR_THEME")
    return (value or DEFAULT_THEME_ID).strip() or DEFAULT_THEME_ID


def theme_dir(theme_id: str | None = None) -> Path:
    """Return the directory for a theme pack."""
    return project_root() / "themes" / (theme_id or active_theme_id())


def world_dir(theme_id: str | None = None) -> Path:
    """Return the active world-data directory."""
    explicit = _environment_value("ESIMU_WORLD_DIR", "SIMULATOR_WORLD_DIR")
    if explicit and theme_id is None:
        return Path(explicit).expanduser().resolve()
    return theme_dir(theme_id) / "world"


def world_file(filename: str, theme_id: str | None = None) -> Path:
    """Return a file path inside the active world-data directory."""
    return world_dir(theme_id) / filename


def frontend_stat_metadata_output() -> Path:
    """Return where generated frontend stat metadata should be written."""
    explicit = _environment_value(
        "ESIMU_FRONTEND_STAT_OUTPUT", "SIMULATOR_FRONTEND_STAT_OUTPUT"
    )
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (
        project_root()
        / "apps"
        / "starter"
        / "frontend"
        / "src"
        / "data"
        / "statDefinitions.generated.ts"
    )


def frontend_theme_metadata_output() -> Path:
    """Return where generated frontend theme metadata should be written."""
    explicit = _environment_value(
        "ESIMU_FRONTEND_THEME_OUTPUT", "SIMULATOR_FRONTEND_THEME_OUTPUT"
    )
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (
        project_root()
        / "apps"
        / "starter"
        / "frontend"
        / "src"
        / "data"
        / "theme.generated.ts"
    )


def frontend_story_metadata_output() -> Path:
    """Return where generated frontend story metadata should be written."""
    explicit = _environment_value(
        "ESIMU_FRONTEND_STORY_OUTPUT", "SIMULATOR_FRONTEND_STORY_OUTPUT"
    )
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (
        project_root()
        / "apps"
        / "starter"
        / "frontend"
        / "src"
        / "data"
        / "story.generated.ts"
    )
