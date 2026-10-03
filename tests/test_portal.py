from fastapi.testclient import TestClient

from portal.main import app

client = TestClient(app)


def test_latest_is_refused_and_limits_are_rendered():
    refused = client.post("/releases", json={"name": "billing", "image": "billing:latest", "replicas": 2})
    assert refused.status_code == 422
    body = client.post("/releases", json={"name": "billing", "image": "billing:0.1.0", "replicas": 2}).json()
    assert body["applied"] is False
    assert "cpu: 100m" in body["manifest"]
    assert ":latest" not in body["manifest"]
