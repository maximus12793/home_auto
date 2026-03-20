import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from maintenance_orchestrator.api.app import app

@pytest.fixture
def client() -> TestClient:
    db_fd, db_path = tempfile.mkstemp()
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    
    with TestClient(app) as c:
        yield c
        
    os.close(db_fd)
    os.unlink(db_path)
