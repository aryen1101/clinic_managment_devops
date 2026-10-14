def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Clinic Management API"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_reports_database_up(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY", "database": "UP"}


def test_metrics_endpoint_exposes_prometheus_format(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
