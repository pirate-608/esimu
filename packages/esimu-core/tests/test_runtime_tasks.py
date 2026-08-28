"""Tests for runtime background task tracking."""

import asyncio

import pytest

from esimu_core.runtime.tasks import TargetTaskRegistry


@pytest.mark.asyncio
async def test_target_task_registry_deduplicates_running_target() -> None:
    registry = TargetTaskRegistry()
    started = asyncio.Event()
    release = asyncio.Event()

    async def wait_for_release() -> str:
        started.set()
        await release.wait()
        return "done"

    first = registry.track(wait_for_release(), target="relax:walk")
    await started.wait()
    second = registry.track(wait_for_release(), target="relax:walk")

    assert first is not None
    assert second is None
    assert registry.is_inflight("relax:walk") is True

    release.set()
    await first
    await asyncio.sleep(0)

    assert registry.is_inflight("relax:walk") is False
    assert registry.tasks == set()


@pytest.mark.asyncio
async def test_target_task_registry_clears_target_on_failure() -> None:
    registry = TargetTaskRegistry()
    errors: list[BaseException] = []

    async def fail() -> None:
        raise RuntimeError("boom")

    task = registry.track(fail(), target="dingtalk", on_error=errors.append)
    assert task is not None
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert registry.is_inflight("dingtalk") is False
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)


@pytest.mark.asyncio
async def test_cancel_and_wait_drains_tasks_and_targets() -> None:
    registry = TargetTaskRegistry()
    started = asyncio.Event()

    async def wait_forever() -> None:
        started.set()
        await asyncio.Event().wait()

    task = registry.track(wait_forever(), target="messenger:a")
    assert task is not None
    await started.wait()
    await registry.cancel_and_wait()

    assert task.cancelled()
    assert registry.tasks == set()
    assert registry.targets == set()
