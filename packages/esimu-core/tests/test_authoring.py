"""Tests for installed esimu authoring helpers."""

import json
from pathlib import Path
import shutil

import pytest

from esimu_core.authoring import (
    add_world_entry,
    doctor_project,
    inspect_project,
    sync_project_metadata,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(REPO_ROOT / "themes" / "demo-campus", root / "themes" / "demo-campus")
    (root / "apps" / "starter" / "frontend" / "src" / "data").mkdir(parents=True)
    (root / "apps" / "starter" / "frontend" / "package.json").write_text(
        "{}", encoding="utf-8"
    )
    (root / "apps" / "starter" / "backend" / "app").mkdir(parents=True)
    (root / "apps" / "starter" / "backend" / "app" / "main.py").write_text(
        "", encoding="utf-8"
    )
    return root


def test_sync_and_inspect_are_project_local(tmp_path: Path) -> None:
    root = _project(tmp_path)
    before = sync_project_metadata(root, "demo-campus", write=False)
    written = sync_project_metadata(root, "demo-campus", write=True)
    summary = inspect_project(root, "demo-campus")

    assert before["current"] is False
    assert written["mode"] == "write"
    assert sync_project_metadata(root, "demo-campus", write=False)["current"] is True
    assert summary["counts"]["majors"] == 1
    assert summary["counts"]["achievements"] == 2


def test_add_defaults_to_preview_and_writes_valid_item(tmp_path: Path) -> None:
    root = _project(tmp_path)
    sync_project_metadata(root, "demo-campus", write=True)
    item_path = root / "themes" / "demo-campus" / "world" / "items.json"
    original = item_path.read_bytes()
    preview = add_world_entry(
        root,
        "demo-campus",
        "item",
        "focus_card",
        {"name": "Focus Card", "effect": "energy", "effect_value": 5},
        write=False,
    )
    assert preview["write"] is False
    assert item_path.read_bytes() == original

    result = add_world_entry(
        root,
        "demo-campus",
        "item",
        "focus_card",
        {"name": "Focus Card", "effect": "energy", "effect_value": 5},
        write=True,
    )
    items = json.loads(item_path.read_text(encoding="utf-8"))["items"]
    assert result["write"] is True
    assert items[-1]["id"] == "focus_card"


def test_event_preview_matches_starter_two_choice_contract(tmp_path: Path) -> None:
    root = _project(tmp_path)
    preview = add_world_entry(
        root,
        "demo-campus",
        "event",
        "campus_moment",
        {"title": "Campus Moment"},
        write=False,
    )
    assert len(preview["entry"]["options"]) == 2


def test_failed_add_restores_source_and_generated_files(tmp_path: Path) -> None:
    root = _project(tmp_path)
    sync_project_metadata(root, "demo-campus", write=True)
    stat_path = root / "themes" / "demo-campus" / "world" / "stat_definitions.json"
    generated = root / "apps" / "starter" / "frontend" / "src" / "data" / "statDefinitions.generated.ts"
    before = stat_path.read_bytes(), generated.read_bytes()

    with pytest.raises(ValueError):
        add_world_entry(
            root,
            "demo-campus",
            "stat",
            "bad_budget",
            {
                "label": "Bad Budget",
                "default": 1,
                "allocatable": True,
            },
            write=True,
        )
    assert (stat_path.read_bytes(), generated.read_bytes()) == before


def test_doctor_redacts_ai_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _project(tmp_path)
    sync_project_metadata(root, "demo-campus", write=True)
    monkeypatch.setenv("ESIMU_LLM_API_KEY", "secret-value")
    result = doctor_project(root, "demo-campus")
    serialized = json.dumps(result)
    assert result["ai"]["general_configured"] is True
    assert "secret-value" not in serialized
