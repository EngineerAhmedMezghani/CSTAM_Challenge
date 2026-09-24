from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_url_is_rejected_before_database_access():
    response = TestClient(app).post("/api/scrape", json={"url": "file:///tmp/data.html"})
    assert response.status_code == 422


def test_scrape_options_are_validated_before_database_access():
    response = TestClient(app).post(
        "/api/scrape",
        json={"url": "https://example.com", "max_depth": 11, "max_pages": 0},
    )
    assert response.status_code == 422
