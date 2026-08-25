"""Tests for adapter-facing runtime action decisions."""

from esimu_core.domain.actions import ActionDecisionReason
from esimu_core.runtime.actions import decide_runtime_action


def test_running_runtime_allows_gameplay_action() -> None:
    decision = decide_runtime_action("relax", is_running=True)

    assert decision.allowed is True
    assert decision.reason == ActionDecisionReason.ALLOWED


def test_paused_runtime_rejects_gameplay_action() -> None:
    decision = decide_runtime_action("relax", is_running=False)

    assert decision.allowed is False
    assert decision.reason == ActionDecisionReason.PAUSED_GAMEPLAY_ACTION


def test_next_semester_requires_exam_when_stopped() -> None:
    blocked = decide_runtime_action("next_semester", is_running=False)
    allowed = decide_runtime_action(
        "next_semester",
        is_running=False,
        exam_completed=True,
    )

    assert blocked.reason == ActionDecisionReason.NEXT_SEMESTER_REQUIRES_EXAM
    assert allowed.allowed is True

