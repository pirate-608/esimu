"""Smoke tests for project bootstrap tooling."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from esimu_core import __version__

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = BACKEND_ROOT.parents[1]


def test_new_project_generates_valid_standalone_project(tmp_path: Path) -> None:
    """Generated projects should validate and start outside the lab directory."""
    target = tmp_path / "star-lab"
    script = BACKEND_ROOT / "scripts" / "new_project.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(target),
            "--project-name",
            "Star Lab",
            "--theme-id",
            "star-lab",
            "--institution",
            "星河学院",
            "--institution-short",
            "星河",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    theme_path = target / "themes" / "star-lab" / "theme.json"
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    assert theme["theme_id"] == "star-lab"
    assert theme["storage"]["prefix"] == "star_lab"
    assert theme["terms"]["institution"] == "星河学院"

    session = (
        target / "apps" / "starter" / "backend" / "app" / "session.py"
    ).read_text(encoding="utf-8")
    assert 'theme_id: str = "star-lab"' in session
    bootstrap = (
        target / "apps" / "starter" / "backend" / "app" / "bootstrap.py"
    ).read_text(encoding="utf-8")
    assert 'default_theme: str = "star-lab"' in bootstrap
    assert "discover_project_root" in bootstrap

    env_example = (target / ".env.example").read_text(encoding="utf-8")
    assert "ESIMU_CONTENT_MODE=library" in env_example
    assert "ESIMU_RP_MODEL=M2-her" in env_example
    assert "ESIMU_CORS_ORIGINS=" in env_example

    requirements = (
        target / "apps" / "starter" / "backend" / "requirements.txt"
    ).read_text(encoding="utf-8")
    assert "esimu-core[ai] @ git+" in requirements
    assert f"esimu-core-v{__version__}" in requirements

    assert (target / "scripts" / "scaffold_game_stat.py").exists()
    assert (target / "scripts" / "scaffold_world_data.py").exists()
    generated_readme = (target / "README.md").read_text(encoding="utf-8")
    assert "esimu-validate-world --root . --theme star-lab" in generated_readme
    assert "path-to-esimu-lab" not in generated_readme
    generated_agent = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "<project-name>" not in generated_agent
    assert "path-to-esimu" not in generated_agent

    generated_theme = (
        target / "apps" / "starter" / "frontend" / "src" / "data" / "theme.generated.ts"
    ).read_text(encoding="utf-8")
    assert '"theme_id": "star-lab"' in generated_theme

    env = {
        **os.environ,
        "SIMULATOR_LAB_ROOT": str(target),
        "SIMULATOR_THEME": "star-lab",
    }
    validation = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "scripts" / "validate_world_data.py")],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert validation.returncode == 0, validation.stderr

    standalone_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"SIMULATOR_LAB_ROOT", "SIMULATOR_THEME"}
    }
    standalone_env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(BACKEND_ROOT), standalone_env.get("PYTHONPATH", "")])
    )
    standalone = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from fastapi.testclient import TestClient; "
                "from app.main import app; "
                "assert TestClient(app).get('/healthz').json() == "
                "{'status': 'ok'}"
            ),
        ],
        cwd=target / "apps" / "starter" / "backend",
        env=standalone_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert standalone.returncode == 0, standalone.stderr


def test_scaffold_world_data_prints_item_template() -> None:
    """World-data scaffolding should produce reviewable JSON snippets."""
    script = BACKEND_ROOT / "scripts" / "scaffold_world_data.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "item",
            "focus_card",
            "--name",
            "专注卡",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["id"] == "focus_card"
    assert payload["name"] == "专注卡"
    assert payload["effects"]