"""Subprocess coverage for installed-style esimu commands."""

import os
from pathlib import Path
import subprocess
import sys

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