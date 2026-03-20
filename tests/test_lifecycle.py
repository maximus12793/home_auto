import pytest

from maintenance_orchestrator.models.domain import OrchestratorState
from maintenance_orchestrator.state.lifecycle import assert_transition_allowed


def test_valid_transition() -> None:
    assert_transition_allowed(OrchestratorState.intake, OrchestratorState.triage)


def test_invalid_transition() -> None:
    with pytest.raises(ValueError):
        assert_transition_allowed(OrchestratorState.intake, OrchestratorState.completed)
