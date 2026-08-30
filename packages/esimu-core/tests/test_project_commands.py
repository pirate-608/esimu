"""Tests for installed project lifecycle commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from esimu_core import project


def _project_layout(tmp_path: Path) -> project.ProjectLayout:
    (tmp_path / "apps" / "starter" / "backend" / "app").mkdir(parents=True)
    (tmp_path / "apps" / "starter" / "backend" / "app" / "main.py").touch()
    (tmp_path / "apps" / "starter" / "frontend").mkdir(parents=True)
    (tmp_path / "apps" / "starter" / "frontend" / "package.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (tmp_path / "themes" / "test-theme").mkdir(parents=True)
    return project.ProjectLayout.from_root(tmp_path)


def test_build_project_prepares_python_and_frontend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _project_layout(tmp_path)
    commands: list[tuple[list[str], Path]] = []
    monkeypatch.setattr(project, "_prepare_project", lambda *_args: None)
    monkeypatch.setattr(
        project,
        "_ensure_frontend_dependencies",
        lambda *_args, **_kwargs: "corepack",
    )
    monkeypatch.setattr(
        project,
        "_run_checked",
        lambda command, *, cwd, environment: commands.append((list(command), cwd)),
    )

    output = project.build_project(layout.root, "test-theme", install=False)

    assert output == layout.frontend / "dist"
    assert commands[0][0][1:4] == ["-m", "compileall", "-q"]
    assert commands[0][1] == layout.backend
    assert commands[1] == (["corepack", "pnpm", "build"], layout.frontend)
    build = json.loads(
        (layout.state_dir / "build.json").read_text(encoding="utf-8")
    )
    assert build["theme"] == "test-theme"


def test_reload_requires_live_session_and_writes_trigger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _project_layout(tmp_path)
    monkeypatch.setattr(project, "_prepare_project", lambda *_args: None)
    monkeypatch.setattr(project, "_process_exists", lambda pid: pid == 4321)
    layout.state_dir.mkdir()
    layout.session_file.write_text('{"manager_pid": 4321}\n', encoding="utf-8")

    trigger = project.request_dev_reload(layout.root, "test-theme")

    assert trigger == layout.reload_trigger
    payload = json.loads(trigger.read_text(encoding="utf-8"))
    assert payload["requested_by"] == os.getpid()


def test_reload_rejects_missing_dev_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _project_layout(tmp_path)
    monkeypatch.setattr(project, "_prepare_project", lambda *_args: None)

    with pytest.raises(project.ProjectCommandError, match="no active"):
        project.request_dev_reload(layout.root, "test-theme")


def test_dev_supervisor_restarts_when_trigger_changes(
    tmp_path: Path,
) -> None:
    layout = _project_layout(tmp_path)
    started: list[tuple[list[str], dict[str, Any]]] = []
    stop_calls: list[int] = []

    class FakeProcess:
        def __init__(self, pid: int) -> None:
            self.pid = pid

        def poll(self) -> None:
            return None

    def fake_popen(command: list[str], **kwargs: Any) -> FakeProcess:
        started.append((command, kwargs))
        return FakeProcess(1000 + len(started))

    sleeps = 0

    def fake_sleep(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 1:
            project._atomic_write_json(
                layout.reload_trigger, {"requested_at": 1.0}
            )
            return
        if sleeps == 2:
            return
        raise KeyboardInterrupt

    class TestSupervisor(project.DevSupervisor):
        def _stop(self) -> None:
            stop_calls.append(len(self._processes))
            self._processes = []

    specs = (
        project._ProcessSpec("backend", ("python", "backend"), layout.backend),
        project._ProcessSpec("frontend", ("pnpm", "dev"), layout.frontend),
    )
    supervisor = TestSupervisor(
        layout,
        "test-theme",
        specs,
        popen=fake_popen,
        sleep=fake_sleep,
    )

    assert supervisor.run() == 0
    assert len(started) == 4
    assert stop_calls == [2, 2]
    assert not layout.session_file.exists()
