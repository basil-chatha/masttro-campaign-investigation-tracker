"""
Tests for cross-cutting FastAPI app behavior:
- 503 contract when the database is not configured
- CORS middleware (workshop allow_origins=["*"])
- OpenAPI / route registration

These cover invariants that are easy to break accidentally — a refactor
of database.py, a tightened CORS config, or a forgotten include_router()
would all silently change the frontend contract.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 503 / RuntimeError handler
# ---------------------------------------------------------------------------

def test_db_route_returns_503_when_database_url_missing(monkeypatch):
    """Without DATABASE_URL, /campaigns must return 503 with a JSON body.

    This is the lazy-DB contract that the frontend and the existing
    test_health.py already lean on. This test pins the *shape* of the 503
    response (JSON `detail` field) so changes to the exception handler
    don't silently break clients.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Force re-init so any previously cached engine is discarded.
    import app.database as database_module
    database_module._engine = None
    database_module._SessionLocal = None
    database_module.DATABASE_URL = None

    response = client.get("/campaigns")
    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "DATABASE_URL" in body["detail"]


def test_runtime_error_handler_uses_json(monkeypatch):
    """The 503 response must be application/json, not HTML."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import app.database as database_module
    database_module._engine = None
    database_module._SessionLocal = None
    database_module.DATABASE_URL = None

    response = client.get("/campaigns")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def test_cors_preflight_is_allowed():
    """OPTIONS preflight from any origin must succeed under allow_origins=*.

    The frontend Vite dev server uses /api proxy in dev (same-origin),
    but production hosts and ad-hoc tooling rely on CORS. If someone
    tightens the CORS config without updating the frontend, this fails.
    """
    response = client.options(
        "/campaigns",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # Starlette returns 200 for a successful preflight via CORSMiddleware.
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("*", "http://example.com")
    allow_methods = response.headers.get("access-control-allow-methods", "")
    # GET should be in the allowed methods (allow_methods=["*"]).
    assert "GET" in allow_methods or allow_methods == "*"


def test_cors_simple_request_returns_allow_origin_header():
    """A simple GET with an Origin header must echo the CORS allow header."""
    response = client.get("/health", headers={"Origin": "http://example.com"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in (
        "*",
        "http://example.com",
    )


# ---------------------------------------------------------------------------
# Route registration / OpenAPI
# ---------------------------------------------------------------------------

def test_openapi_schema_is_served():
    """/openapi.json must be available and well-formed."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Campaign Investigation Tracker API"
    assert schema["info"]["version"] == "0.1.0"


def test_campaigns_route_is_registered_in_openapi():
    """If someone forgets app.include_router(campaigns.router), this fails.

    Catches a real mistake from the workshop add-a-resource flow.
    """
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/campaigns" in paths
    assert "get" in paths["/campaigns"]


def test_campaigns_route_is_tagged_correctly():
    """The router declares tags=["campaigns"] — the frontend SDK gen relies on this."""
    response = client.get("/openapi.json")
    op = response.json()["paths"]["/campaigns"]["get"]
    assert "campaigns" in op.get("tags", [])


def test_campaign_out_schema_is_in_components():
    """CampaignOut should be present as a referenced response model."""
    response = client.get("/openapi.json")
    schemas = response.json().get("components", {}).get("schemas", {})
    assert "CampaignOut" in schemas
    properties = schemas["CampaignOut"]["properties"]
    # Pin the field set the frontend depends on.
    expected_fields = {
        "id", "campaign_code", "name", "advertiser", "status", "objective",
        "channel", "start_date", "end_date", "budget_usd", "owner_name",
        "region", "created_at", "updated_at",
    }
    assert expected_fields.issubset(set(properties.keys()))


def test_health_route_is_not_tied_to_database():
    """/health must respond regardless of DATABASE_URL state.

    Health is what monitors and load balancers hit; if we accidentally
    add a DB dependency, the app will look unhealthy whenever Postgres
    blips.
    """
    # No monkeypatch — we just want to assert /health never 503s.
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
