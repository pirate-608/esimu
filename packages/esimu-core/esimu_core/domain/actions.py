"""Pure runtime action-gating rules for simulator engines.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.
The rules here do not know about WebSocket, Redis, or UI copy. They only answer
whether an action may mutate gameplay under the current engine state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ActionDecisionReason(StrEnum):
    """Machine-readable reason for an action gate decision."""

    ALLOWED = "allowed"
    PAUSED_GAMEPLAY_ACTION = "paused_gameplay_action"
    NEXT_SEMESTER_REQUIRES_EXAM = "next_semester_requires_exam"
    UNKNOWN_WHILE_PAUSED = "unknown_while_paused"


@dataclass(frozen=True)
class ActionGateDecision:
    """Result of checking one action against engine runtime state."""

    allowed: bool
    reason: ActionDecisionReason = ActionDecisionReason.ALLOWED


ALWAYS_ALLOWED_WHILE_STOPPED = frozenset(
    {
        "start",
        "get_state",
        "pause",
        "resume",
        "restart",
        "set_speed",
        "set_mode",
        "messenger_mark_read",
        "dingtalk_mark_read",
    }
)

GAMEPLAY_MUTATION_ACTIONS = frozenset(
    {
        "relax",
        "exam",
        "event_choice",
        "messenger_reply",
        "dingtalk_reply",
        "item_buy",
        "item_sell",
        "change_course_state",
    }
)


def runtime_action_decision(
    action: object,
    *,
    is_running: bool,
    exam_completed: bool = False,
) -> ActionGateDecision:
    """Return whether an action can run under the current runtime state."""
    if is_running:
        return ActionGateDecision(True)

    action_name = str(action or "")
    if action_name in ALWAYS_ALLOWED_WHILE_STOPPED:
        return ActionGateDecision(True)

    if action_name == "next_semester":
        if exam_completed:
            return ActionGateDecision(True)
        return ActionGateDecision(
            False,
            ActionDecisionReason.NEXT_SEMESTER_REQUIRES_EXAM,
        )

    if action_name in GAMEPLAY_MUTATION_ACTIONS:
        return ActionGateDecision(False, ActionDecisionReason.PAUSED_GAMEPLAY_ACTION)

    return ActionGateDecision(False, ActionDecisionReason.UNKNOWN_WHILE_PAUSED)

