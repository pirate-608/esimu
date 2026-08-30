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
PROJECT_ROOT = BACKEND_ROOT.parents[1]
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
            cwd=PROJECT_ROOT,
        )
        wheels = sorted(dist.glob("esimu_core-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one wheel, found: {wheels}")
        wheel_dependency = f"esimu-core[ai] @ {wheels[0].as_uri()}"
        _run([sys.executable, "-m", "venv", str(venv)], cwd=PROJECT_ROOT)
        python = _venv_python(venv)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                wheel_dependency,
            ],
            cwd=temp,
        )
        _run(
            [
                str(python),
                "-m",
                "esimu_core.cli",
                "new",
                str(project),
                "--project-name",
                "Release Smoke",
                "--theme-id",
                "release-smoke",
                "--core-dependency",
                wheel_dependency,
            ],
            cwd=temp,
        )
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
                "validate",
                "--root",
                str(project),
                "--theme",
                "release-smoke",
            ],
            cwd=temp,
        )
        for command in (
            ["doctor", "--root", str(project), "--theme", "release-smoke"],
            ["inspect", "--root", str(project), "--theme", "release-smoke", "--json"],
            ["sync", "--root", str(project), "--theme", "release-smoke"],
            [
                "add",
                "item",
                "smoke_preview",
                "--root",
                str(project),
                "--theme",
                "release-smoke",
            ],
        ):
            _run(
                [str(python), "-m", "esimu_core.cli", *command],
                cwd=temp,
            )

        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "PYTHONPATH",
                "ESIMU_PROJECT_ROOT",
                "ESIMU_THEME",
                "SIMULATOR_LAB_ROOT",
                "SIMULATOR_THEME",
            }
        }
        clean_env["ESIMU_STARTER_SESSION_STORE"] = "sqlite"
        clean_env["ESIMU_STARTER_DATABASE_PATH"] = str(temp / "smoke.sqlite3")
        smoke_code = """
from fastapi.testclient import TestClient
from app.main import app

def receive_type(websocket, expected):
    for _ in range(30):
        message = websocket.receive_json()
        if message['type'] == expected:
            return message
    raise AssertionError(expected)

with TestClient(app) as client:
    assert client.get('/healthz').json() == {
        'status': 'ok',
        'storage': 'ready',
    }
    token = client.post(
        '/api/auth', json={'username': 'Release'}
    ).json()['token']
    major = client.get('/api/majors').json()[0]['abbr']
    response = client.post(
        '/api/init_character',
        json={'token': token, 'username': 'Release', 'major': major},
    )
    assert response.status_code == 200
    with client.websocket_connect('/ws') as websocket:
        websocket.send_json({'token': token, 'protocol_version': 2})
        receive_type(websocket, 'auth_ok')
        receive_type(websocket, 'init')
        websocket.send_json({'action': 'exam'})
        assert receive_type(websocket, 'semester_summary')['data']['ended'] is False
        websocket.send_json({'action': 'next_semester'})
        receive_type(websocket, 'new_semester')
        websocket.send_json({'action': 'exam'})
        assert receive_type(websocket, 'semester_summary')['data']['ended'] is True
        websocket.send_json({'action': 'ending'})
        assert receive_type(websocket, 'ending')['data']['outcome'] == 'graduation'
        websocket.send_json({'action': 'save_game'})
        assert receive_type(websocket, 'save_result')['success'] is True

with TestClient(app) as client:
    resumed = client.post('/api/auth', json={'username': 'Release', 'token': token})
    assert resumed.json()['status'] == 'returning'
"""
        _run(
            [str(python), "-c", smoke_code],
            cwd=project / "apps" / "starter" / "backend",
            env=clean_env,
        )

    print("release smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
