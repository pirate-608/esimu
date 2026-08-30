"""Project-level development, build, and reload orchestration for esimu.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The core package owns orchestration decisions but does not import FastAPI,
Vite, or application modules. Commands execute tools installed by the generated
Starter project and keep their process state under ``.esimu``.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Sequence

from esimu_core import __version__


class ProjectCommandError(RuntimeError):
    """Raised when a generated project cannot complete a lifecycle command."""


@dataclass(frozen=True)
class ProjectLayout:
    """Resolved paths required by installed project commands."""

    root: Path
    backend: Path
    frontend: Path
    state_dir: Path
    reload_trigger: Path
    session_file: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "ProjectLayout":
        """Resolve and validate a generated esimu project root."""
        project_root = Path(root).expanduser().resolve()
        backend = project_root / "apps" / "starter" / "backend"
        frontend = project_root / "apps" / "starter" / "frontend"
        required = (
            backend / "app" / "main.py",
            frontend / "package.json",
            project_root / "themes",
        )
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise ProjectCommandError(
                "not an esimu Starter project; missing: " + ", ".join(missing)
            )
        state_dir = project_root / ".esimu"
        return cls(
            root=project_root,
            backend=backend,
            frontend=frontend,
            state_dir=state_dir,
            reload_trigger=state_dir / "reload.trigger",
            session_file=state_dir / "dev-session.json",
        )


def _project_environment(layout: ProjectLayout, theme_id: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "ESIMU_PROJECT_ROOT": str(layout.root),
            "ESIMU_THEME": theme_id,
            "PYTHONUNBUFFERED": "1",
        }
    )
    return environment


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _prepare_project(layout: ProjectLayout, theme_id: str) -> None:
    """Synchronize generated metadata and reject an invalid active theme."""
    os.environ["ESIMU_PROJECT_ROOT"] = str(layout.root)
    os.environ["ESIMU_THEME"] = theme_id

    from esimu_core.authoring import sync_project_metadata
    from esimu_core.world.validation import validate_theme_data

    sync_project_metadata(layout.root, theme_id, write=True)
    errors = validate_theme_data(layout.root, theme_id)
    if errors:
        raise ProjectCommandError("theme validation failed: " + "; ".join(errors))


def _resolve_command(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise ProjectCommandError(f"required command is unavailable: {name}")
    return executable


def _run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> None:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        env=environment,
        check=False,
    )
    if result.returncode:
        raise ProjectCommandError(
            f"command failed with exit code {result.returncode}: "
            + " ".join(command)
        )


def _ensure_frontend_dependencies(
    layout: ProjectLayout,
    environment: dict[str, str],
    *,
    install: bool,
) -> str:
    corepack = _resolve_command("corepack")
    if (layout.frontend / "node_modules").is_dir():
        return corepack
    if not install:
        raise ProjectCommandError(
            "frontend dependencies are missing; rerun without --no-install"
        )
    _run_checked(
        [corepack, "pnpm", "install", "--frozen-lockfile"],
        cwd=layout.frontend,
        environment=environment,
    )
    return corepack


def build_project(
    root: str | Path,
    theme_id: str,
    *,
    install: bool = True,
) -> Path:
    """Validate a project and create its production frontend bundle."""
    layout = ProjectLayout.from_root(root)
    _prepare_project(layout, theme_id)
    environment = _project_environment(layout, theme_id)
    _run_checked(
        [sys.executable, "-m", "compileall", "-q", "app"],
        cwd=layout.backend,
        environment=environment,
    )
    corepack = _ensure_frontend_dependencies(
        layout,
        environment,
        install=install,
    )
    _run_checked(
        [corepack, "pnpm", "build"],
        cwd=layout.frontend,
        environment=environment,
    )
    output = layout.frontend / "dist"
    _atomic_write_json(
        layout.state_dir / "build.json",
        {
            "core_version": __version__,
            "theme": theme_id,
            "output": str(output),
            "built_at": time.time(),
        },
    )
    return output


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def request_dev_reload(root: str | Path, theme_id: str) -> Path:
    """Synchronize content and request a running ``esimu dev`` restart."""
    layout = ProjectLayout.from_root(root)
    _prepare_project(layout, theme_id)
    try:
        session = json.loads(layout.session_file.read_text(encoding="utf-8"))
        manager_pid = int(session["manager_pid"])
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ProjectCommandError("no active esimu dev session was found") from None
    if not _process_exists(manager_pid):
        raise ProjectCommandError(
            "the recorded esimu dev session is no longer running"
        )
    _atomic_write_json(
        layout.reload_trigger,
        {"requested_at": time.time(), "requested_by": os.getpid()},
    )
    return layout.reload_trigger


@dataclass(frozen=True)
class _ProcessSpec:
    name: str
    command: tuple[str, ...]
    cwd: Path


class DevSupervisor:
    """Run and restart the Starter backend and frontend as one foreground job."""

    def __init__(
        self,
        layout: ProjectLayout,
        theme_id: str,
        specs: Sequence[_ProcessSpec],
        *,
        popen: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.layout = layout
        self.theme_id = theme_id
        self.specs = tuple(specs)
        self._popen = popen
        self._sleep = sleep
        self._processes: list[tuple[_ProcessSpec, subprocess.Popen[Any]]] = []
        self._trigger_mtime = 0

    def _start(self) -> None:
        environment = _project_environment(self.layout, self.theme_id)
        self._processes = []
        for spec in self.specs:
            kwargs: dict[str, Any] = {
                "cwd": spec.cwd,
                "env": environment,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True
            process = self._popen(list(spec.command), **kwargs)
            self._processes.append((spec, process))
        self._trigger_mtime = self._reload_mtime()
        _atomic_write_json(
            self.layout.session_file,
            {
                "manager_pid": os.getpid(),
                "theme": self.theme_id,
                "started_at": time.time(),
                "processes": {
                    spec.name: process.pid for spec, process in self._processes
                },
            },
        )

    def _reload_mtime(self) -> int:
        try:
            return self.layout.reload_trigger.stat().st_mtime_ns
        except FileNotFoundError:
            return 0

    def _stop(self) -> None:
        for _spec, process in reversed(self._processes):
            if process.poll() is not None:
                continue
            if os.name == "nt":
                try:
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        check=False,
                        capture_output=True,
                    )
            else:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        self._processes = []

    def run(self) -> int:
        """Run until interrupted, a child exits, or reload restarts the pair."""
        self.layout.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._start()
            while True:
                for spec, process in self._processes:
                    return_code = process.poll()
                    if return_code is not None:
                        raise ProjectCommandError(
                            f"{spec.name} exited with code {return_code}"
                        )
                current_mtime = self._reload_mtime()
                if current_mtime > self._trigger_mtime:
                    print("reload requested; restarting esimu development services")
                    self._stop()
                    self._sleep(0.5)
                    self._start()
                self._sleep(0.5)
        except KeyboardInterrupt:
            return 0
        finally:
            self._stop()
            try:
                session = json.loads(
                    self.layout.session_file.read_text(encoding="utf-8")
                )
                if int(session.get("manager_pid", -1)) == os.getpid():
                    self.layout.session_file.unlink(missing_ok=True)
            except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError):
                pass


def run_dev_project(
    root: str | Path,
    theme_id: str,
    *,
    backend_host: str = "127.0.0.1",
    backend_port: int = 18001,
    frontend_host: str = "127.0.0.1",
    frontend_port: int = 15175,
    install: bool = True,
) -> int:
    """Prepare and run the backend and frontend development servers."""
    layout = ProjectLayout.from_root(root)
    _prepare_project(layout, theme_id)
    environment = _project_environment(layout, theme_id)
    _ensure_frontend_dependencies(
        layout,
        environment,
        install=install,
    )
    node = _resolve_command("node")
    vite_entry = layout.frontend / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite_entry.is_file():
        raise ProjectCommandError(f"Vite entry point is missing: {vite_entry}")
    specs = (
        _ProcessSpec(
            "backend",
            (
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                backend_host,
                "--port",
                str(backend_port),
            ),
            layout.backend,
        ),
        _ProcessSpec(
            "frontend",
            (
                node,
                str(vite_entry),
                "--host",
                frontend_host,
                "--port",
                str(frontend_port),
                "--strictPort",
            ),
            layout.frontend,
        ),
    )
    print(f"backend: http://{backend_host}:{backend_port}")
    print(f"frontend: http://{frontend_host}:{frontend_port}")
    print("press Ctrl+C to stop; run `esimu reload` in another terminal to restart")
    return DevSupervisor(layout, theme_id, specs).run()
