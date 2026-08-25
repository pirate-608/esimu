"""Tests for esimu-core package metadata."""

import tomllib
from importlib.metadata import version
from pathlib import Path

import esimu_core

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_version_matches_package_metadata() -> None:
    """Keep import-time and package metadata versions in sync."""
    assert esimu_core.__version__ == version("esimu-core")


def test_dev_extra_includes_starter_smoke_dependencies() -> None:
    """Keep clean-runner dependencies used by the bootstrap smoke explicit."""
    metadata = tomllib.loads(
        (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = metadata["project"]["optional-dependencies"]["dev"]

    assert any(dependency.startswith("fastapi") for dependency in dependencies)
    assert any(dependency.startswith("httpx") for dependency in dependencies)
