from fastapi.testclient import TestClient

from backend.app.main import app


def test_health():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
