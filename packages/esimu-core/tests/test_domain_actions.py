"""Regression tests for pure runtime action-gating rules."""

from esimu_core.domain.actions import (
    ActionDecisionReason,
    runtime_action_decision,
)


def test_running_engine_allows_actions() -> None:
    decision = runtime_action_decision("relax", is_running=True)

    assert decision.allowed is True
    assert decision.reason == ActionDecisionReason.ALLOWED


def test_paused_engine_allows_navigation_actions() -> None:
    for action in ("start", "get_state", "resume", "restart", "set_mode"):
        assert runtime_action_decision(action, is_running=False).allowed is True


def test_paused_engine_blocks_gameplay_mutations() -> None:
    decision = runtime_action_decision("item_buy", is_running=False)

    assert decision.allowed is False
    assert decision.reason == ActionDecisionReason.PAUSED_GAMEPLAY_ACTION


def test_next_semester_requires_exam_while_stopped() -> None:
    blocked = runtime_action_decision(
        "next_semester",
        is_running=False,
        exam_completed=False,
    )
    allowed = runtime_action_decision(
        "next_semester",
        is_running=False,
        exam_completed=True,
    )

    assert blocked.allowed is False
    assert blocked.reason == ActionDecisionReason.NEXT_SEMESTER_REQUIRES_EXAM
    assert allowed.allowed is True


