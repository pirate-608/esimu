"""Tests for installed project-local world validation."""

from pathlib import Path

from esimu_core.world.validation import main, validate_theme_data

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = BACKEND_ROOT.parents[1]


def test_demo_theme_validates_through_package_api() -> None:
    assert validate_theme_data(LAB_ROOT, "demo-campus") == []


def test_validation_command_accepts_explicit_root_and_theme() -> None:
    assert main(["--root", str(LAB_ROOT), "--theme", "demo-campus"]) == 0