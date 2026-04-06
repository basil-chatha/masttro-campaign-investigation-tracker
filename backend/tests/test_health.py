"""
Tests for health and basic connectivity.
These tests verify the API is structured correctly.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Test that /health endpoint returns 200 status code."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_correct_json():
    """Test that /health endpoint returns expected JSON structure."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "campaign-investigation-tracker"


def test_root_endpoint_returns_200():
    """Test that / endpoint returns 200 status code."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_returns_api_info():
    """Test that / endpoint returns API info."""
    response = client.get("/")
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_campaigns_endpoint_exists():
    """Test that /campaigns endpoint exists and is routable."""
    response = client.get("/campaigns")
    # 200 if database is connected, 503 if DATABASE_URL is not set.
    # Either way, the route exists and FastAPI handled it gracefully.
    assert response.status_code in [200, 503]


def test_docs_endpoint_exists():
    """Test that Swagger UI is available at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_ai_runs_endpoint_exists():
    """Test that /ai-runs endpoint exists and is routable."""
    response = client.get("/ai-runs")
    assert response.status_code in [200, 503]


def test_campaign_detail_endpoint_exists():
    """Test that GET /campaigns/{id} is routable."""
    response = client.get("/campaigns/cmp_1001")
    assert response.status_code in [200, 404, 503]


def test_campaign_health_endpoint_exists():
    """Test that GET /campaigns/{id}/health is routable."""
    response = client.get("/campaigns/cmp_1001/health")
    assert response.status_code in [200, 404, 503]


def test_investigations_list_endpoint_exists():
    """Test that GET /investigations endpoint exists and is routable."""
    response = client.get("/investigations")
    assert response.status_code in [200, 503]


def test_create_investigation_endpoint_exists():
    """Test that POST /investigations is routable."""
    response = client.post("/investigations", json={
        "campaign_id": "cmp_1001",
        "issue_type": "Test",
        "severity": "Low",
        "question": "Test question?",
        "hypothesis": "Test hypothesis",
        "next_action": "Test action",
    })
    assert response.status_code in [200, 404, 422, 503]


def test_campaign_investigations_endpoint_exists():
    """Test that GET /campaigns/{id}/investigations is routable."""
    response = client.get("/campaigns/cmp_1001/investigations")
    assert response.status_code in [200, 404, 503]


# TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add test_investigation_status_update().
#   Verify PATCH /investigations/{id}/status route exists and handles status transitions.
#   This test can be developed as one of the parallel work streams (backend status logic).


# TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Consider creating a separate
#   test file `tests/test_investigations.py` for investigation-specific tests.
#   Parallel work split: one stream handles backend logic, one handles tests.
