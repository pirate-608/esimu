"""Background task tracking helpers for runtime adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any


TaskErrorHandler = Callable[[BaseException], None]


class TargetTaskRegistry:
    """Track background tasks and optional per-target in-flight keys."""

    def __init__(self) -> None:
        self.tasks: set[asyncio.Task[Any]] = set()
        self.targets: set[str] = set()

    def is_inflight(self, target: str) -> bool:
        """Return whether a target currently has a running task."""
        return target in self.targets

    def track(
        self,
        coro: Coroutine[Any, Any, Any],
        *,
        target: str | None = None,
        on_error: TaskErrorHandler | None = None,
    ) -> asyncio.Task[Any] | None:
        """Create and track a task, de-duplicating by target when provided."""
        if target and target in self.targets:
            coro.close()
            return None

        if target:
            self.targets.add(target)
        task = asyncio.create_task(coro)
        self.tasks.add(task)

        def _finalize_background_task(done_task: asyncio.Task[Any]) -> None:
            self.tasks.discard(done_task)
            if target:
                self.targets.discard(target)
            try:
                done_task.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # pragma: no cover - handler decides logging.
                if on_error is not None:
                    on_error(exc)

        task.add_done_callback(_finalize_background_task)
        return task

    def cancel_all(self) -> None:
        """Cancel all tracked tasks and clear target bookkeeping."""
        for task in list(self.tasks):
            task.cancel()
        self.tasks.clear()
        self.targets.clear()

