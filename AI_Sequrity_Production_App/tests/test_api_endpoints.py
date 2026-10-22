from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert "Enterprise" in res.json()["message"]


def test_health_endpoints():
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = client.get("/health/ready")
    assert ready.status_code in [200, 503]
    assert ready.json()["status"] in ["ready", "not_ready"]
