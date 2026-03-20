from __future__ import annotations

from maintenance_orchestrator.models.domain import (
    BlockedBy,
    MaintenanceRequest,
    OrchestratorState,
)


_ALLOWED: dict[OrchestratorState, frozenset[OrchestratorState]] = {
    OrchestratorState.intake: frozenset(
        {
            OrchestratorState.triage,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.triage: frozenset(
        {
            OrchestratorState.research,
            OrchestratorState.quoting,
            OrchestratorState.vendor_selected,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.research: frozenset(
        {
            OrchestratorState.quoting,
            OrchestratorState.vendor_selected,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.quoting: frozenset(
        {
            OrchestratorState.vendor_selected,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.vendor_selected: frozenset(
        {
            OrchestratorState.scheduled,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.scheduled: frozenset(
        {
            OrchestratorState.in_progress,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.in_progress: frozenset(
        {
            OrchestratorState.completed,
            OrchestratorState.cancelled,
        }
    ),
    OrchestratorState.completed: frozenset(),
    OrchestratorState.cancelled: frozenset(),
}


def assert_transition_allowed(current: OrchestratorState, new: OrchestratorState) -> None:
    allowed = _ALLOWED.get(current, frozenset())
    if new not in allowed:
        raise ValueError(f"Invalid transition {current.value} -> {new.value}")


def apply_blocked_flags_for_state(req: MaintenanceRequest) -> MaintenanceRequest:
    """Keep blocked_by / awaiting_tenant coherent with state (minimal defaults)."""
    r = req.model_copy(deep=True)
    if r.state in (OrchestratorState.completed, OrchestratorState.cancelled):
        r.blocked_by = BlockedBy.none
        r.awaiting_tenant = False
        r.awaiting_tenant_reason = None
        r.next_action = None
    return r
