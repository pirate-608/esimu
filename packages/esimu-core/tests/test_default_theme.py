"""Coverage for the self-contained default ZJU simplified theme."""

from __future__ import annotations

from pathlib import Path

from esimu_core.world.catalog import WorldCatalog
from esimu_core.world.theme_paths import DEFAULT_THEME_ID
from esimu_core.world.validation import validate_theme_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_zju_simplified_is_valid_default_theme() -> None:
    assert DEFAULT_THEME_ID == "zju-simplified"
    assert validate_theme_data(PROJECT_ROOT, DEFAULT_THEME_ID) == []

    catalog = WorldCatalog(DEFAULT_THEME_ID)
    assignment = catalog.major_assignment("CS")

    assert assignment is not None
    assert assignment["major_info"]["name"] == "计算机科学与技术"
    assert len(assignment["initial_courses"]) == 3
    assert catalog.achievements()["steady_graduate"]["name"] == "求是鹰飞"
