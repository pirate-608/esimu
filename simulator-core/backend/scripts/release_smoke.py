"""Build and exercise esimu as an external generated project.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = BACKEND_ROOT.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> None:
    print(f"[{cwd}] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _check_release_tag() -> None:
    ref_type = os.environ.get("GITHUB_REF_TYPE")
    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_type != "tag" or not ref_name:
        return

    from esimu_core import __version__

    expected = f"esimu-core-v{__version__}"
    if ref_name != expected:
        raise RuntimeError(f"release tag {ref_name!r} must equal {expected!r}")


def main() -> int:
    """Run a wheel-to-generated-project smoke in disposable directories."""
    _check_release_tag()
    with tempfile.TemporaryDirectory(prefix="esimu-release-") as temp_dir:
        temp = Path(temp_dir)
        dist = temp / "dist"
        project = temp / "generated-simulator"
        venv = temp / "venv"

        _run(
            [
                sys.executable,
                "-m",
                "build",
                "--outdir",
                str(dist),
                str(BACKEND_ROOT),
            ],
            cwd=LAB_ROOT,
        )
        wheels = sorted(dist.glob("esimu_core-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one wheel, found: {wheels}")
        wheel_dependency = f"esimu-core[ai] @ {wheels[0].as_uri()}"

        _run(
            [
                sys.executable,
                str(BACKEND_ROOT / "scripts" / "new_project.py"),
                str(project),
                "--project-name",
                "Release Smoke",
                "--theme-id",
                "release-smoke",
                "--core-dependency",
                wheel_dependency,
            ],
            cwd=LAB_ROOT,
        )
        _run([sys.executable, "-m", "venv", str(venv)], cwd=LAB_ROOT)
        python = _venv_python(venv)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(project / "apps" / "starter" / "backend" / "requirements.txt"),
            ],
            cwd=project,
        )
        _run(
            [
                str(python),
                "-m",
                "esimu_core.cli",
                "--root",
                str(project),
                "--theme",
                "release-smoke",
            ],
            cwd=temp,
        )

        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONPATH", "SIMULATOR_LAB_ROOT", "SIMULATOR_THEME"}
        }
        smoke_code = (
            "from fastapi.testclient import TestClient; "
            "from app.main import app; "
            "client=TestClient(app); "
            "assert client.get('/healthz').json() == {'status': 'ok'}; "
            "token=client.post('/api/auth', json={'username':'Release'}).json()['token']; "
            "response=client.post('/api/init_character', "
            "json={'token':token,'username':'Release','major':'GEN'}); "
            "assert response.status_code == 200"
        )
        _run(
            [str(python), "-c", smoke_code],
            cwd=project / "apps" / "starter" / "backend",
            env=clean_env,
        )

    print("release smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())