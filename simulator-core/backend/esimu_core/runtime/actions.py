"""Runtime-facing action decisions for simulator adapters."""

from __future__ import annotations

from dataclasses import dataclass

from esimu_core.domain.actions import ActionDecisionReason, runtime_action_decision


@dataclass(frozen=True)
class RuntimeActionDecision:
    """Adapter-facing result for deciding whether to handle an action."""

    action: str
    allowed: bool
    reason: ActionDecisionReason


def decide_runtime_action(
    action: object,
    *,
    is_running: bool,
    exam_completed: bool = False,
) -> RuntimeActionDecision:
    """Return a normalized action decision for runtime adapters."""
    action_name = str(action or "")
    decision = runtime_action_decision(
        action_name,
        is_running=is_running,
        exam_completed=exam_completed,
    )
    return RuntimeActionDecision(
        action=action_name,
        allowed=decision.allowed,
        reason=decision.reason,
    )

