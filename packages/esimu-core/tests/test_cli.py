"""Subprocess coverage for installed-style esimu commands."""

import os
from pathlib import Path
import subprocess
import sys

from esimu_core.cli import main

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = BACKEND_ROOT.parents[1]


def test_validate_world_cli_sets_root_before_world_imports(tmp_path: Path) -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"SIMULATOR_LAB_ROOT", "SIMULATOR_THEME"}
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "esimu_core.cli",
            "--root",
            str(LAB_ROOT),
            "--theme",
            "demo-campus",
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "world data validation passed: demo-campus" in result.stdout


def test_inspect_command_supports_json(capsys) -> None:
    result = main(
        ["inspect", "--root", str(LAB_ROOT), "--theme", "demo-campus", "--json"]
    )
    payload = capsys.readouterr().out
    assert result == 0
    assert '"themeId": "demo-campus"' in payload


def test_add_command_is_dry_run_without_write(capsys) -> None:
    result = main(
        [
            "add",
            "item",
            "preview_item",
            "--root",
            str(LAB_ROOT),
            "--theme",
            "demo-campus",
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert '"write": false' in output
    assert "dry run only" in output
