from fastapi.testclient import TestClient

from maintenance_orchestrator.models.domain import Channel, OrchestratorState


def _sample_intake(portfolio_id: str = "pf-1", property_id: str = "prop-a", unit_id: str = "u-1"):
    return {
        "portfolio_id": portfolio_id,
        "property_id": property_id,
        "unit_id": unit_id,
        "tenant": {"display_name": "Jane D.", "email": "j@example.com", "phone": "+15550001"},
        "channel": Channel.form.value,
        "description": "Kitchen sink is leaking under the cabinet",
        "property_address": "123 Main St",
    }


def test_create_and_list_scoped(client: TestClient) -> None:
    r = client.post("/requests", json=_sample_intake())
    assert r.status_code == 200
    body = r.json()
    cid = body["correlation_id"]
    assert cid.startswith("REQ-")
    assert body["portfolio_id"] == "pf-1"
    assert body["state"] == OrchestratorState.intake.value

    other = client.post(
        "/requests",
        json=_sample_intake(portfolio_id="pf-2", property_id="prop-b", unit_id="u-2"),
    )
    assert other.status_code == 200

    listed = client.get("/requests", params={"portfolio_id": "pf-1"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_triage_and_transition_flow(client: TestClient) -> None:
    cid = client.post("/requests", json=_sample_intake()).json()["correlation_id"]
    tr = client.post(f"/requests/{cid}/triage")
    assert tr.status_code == 200
    assert tr.json()["state"] == OrchestratorState.triage.value
    assert tr.json()["trade"] == "plumbing"

    q = client.post(
        f"/requests/{cid}/transition",
        json={"new_state": OrchestratorState.quoting.value},
    )
    assert q.status_code == 200
    assert q.json()["state"] == OrchestratorState.quoting.value
    assert q.json()["cmms_work_order_id"] is not None


def test_tenant_coordination(client: TestClient) -> None:
    cid = client.post("/requests", json=_sample_intake()).json()["correlation_id"]
    client.post(f"/requests/{cid}/triage")
    r = client.post(
        f"/requests/{cid}/tenant-coordination",
        json={
            "awaiting_tenant": True,
            "reason": "schedule_access",
            "blocked_by": "tenant",
            "next_action": "Call tenant for 2–4pm window",
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j["awaiting_tenant"] is True
    assert j["blocked_by"] == "tenant"


def test_audit_trail(client: TestClient) -> None:
    cid = client.post("/requests", json=_sample_intake()).json()["correlation_id"]
    client.post(f"/requests/{cid}/triage")
    ev = client.get(f"/requests/{cid}/audit")
    assert ev.status_code == 200
    actions = [e["action"] for e in ev.json()]
    assert "request_created" in actions
    assert "triage_completed" in actions
