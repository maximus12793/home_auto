# home_auto — maintenance orchestrator

Implements the routing layer described in [MAINTENANCE_ROUTING_PLAN.md](MAINTENANCE_ROUTING_PLAN.md): portfolio-scoped requests, provenance (who/when/channel), canonical lifecycle + tenant coordination flags, append-only audit events, and stubs for CMMS/vendor connectors.

## Run the API

```bash
cd /path/to/home_auto
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn maintenance_orchestrator.api.app:app --reload
```

## Tests

```bash
pytest
```

- `POST /requests` — intake (requires `portfolio_id`, `property_id`, `unit_id`, tenant, description, channel)
- `GET /requests?portfolio_id=...` — list scoped to a portfolio
- `GET /requests/{correlation_id}` — one request by `REQ-…` id
- `POST /requests/{correlation_id}/triage` — set trade/priority (runs router suggestion)
- `POST /requests/{correlation_id}/transition` — move lifecycle state (validates gates)
- `GET /requests/{correlation_id}/audit` — event stream

## Package layout

| Path | Role |
|------|------|
| `maintenance_orchestrator/models/` | Domain types |
| `maintenance_orchestrator/intake/` | Normalize + correlation id + provenance |
| `maintenance_orchestrator/triage/` | Trade / priority classification |
| `maintenance_orchestrator/router/` | Dispatch path + vendor match (stub rules) |
| `maintenance_orchestrator/state/` | Canonical states, CMMS mapping, `blocked_by` |
| `maintenance_orchestrator/vendors/` | In-memory vendor directory |
| `maintenance_orchestrator/quotes/` | Quote collection stub |
| `maintenance_orchestrator/connectors/` | CMMS connector interface + no-op impl |
| `maintenance_orchestrator/audit/` | Append-only events |
| `maintenance_orchestrator/store/` | Portfolio-scoped in-memory store |
| `maintenance_orchestrator/api/` | FastAPI |

Replace the in-memory store with Postgres/SQLite and wire `connectors` to Atlas CMMS when ready.
