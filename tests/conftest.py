import pytest
from fastapi.testclient import TestClient

from maintenance_orchestrator.api.app import app


@pytest.fixture
def client() -> TestClient:
    # Context manager runs FastAPI lifespan so `_orch` is initialized.
    with TestClient(app) as c:
        yield c
