import json


def test_health_check(client):
    """Basic test to check if the API health endpoint is working."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "status" in data
    assert data["status"] == "ok"
