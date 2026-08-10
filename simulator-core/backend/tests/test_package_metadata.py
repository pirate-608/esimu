"""Tests for esimu-core package metadata."""

from importlib.metadata import version

import esimu_core


def test_runtime_version_matches_package_metadata() -> None:
    """Keep import-time and package metadata versions in sync."""
    assert esimu_core.__version__ == version("esimu-core")
