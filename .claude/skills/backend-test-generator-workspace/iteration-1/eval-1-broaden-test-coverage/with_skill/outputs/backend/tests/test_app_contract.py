"""
Tests for cross-cutting app contracts: the RuntimeError -> 503 handler,
CORS configuration, and the OpenAPI surface.

These contracts are called out in backend/CLAUDE.md as load-bearing for
the workshop (lazy DB init, frontend dev proxy). They have no dedicated
tests today, so a regression — e.g. someone "tightening" CORS, or
removing the exception handler — would slip through silently.
"""
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# RuntimeError -> 503 handler (registered in app/main.py)
# ---------------------------------------------------------------------------


def test_runtime_error_handler_translates_arbitrary_runtime_errors_to_503():
    """The handler must convert any RuntimeError raised inside a request
    into a 503 JSON response, regardless of the route. We register a
    throwaway router to drive this without depending on the DB layer."""

    probe = APIRouter()

    @probe.get("/__runtime_error_probe__")
    def _boom():
        raise RuntimeError("synthetic failure")

    app.include_router(probe)
    try:
        response = client.get("/__runtime_error_probe__")
    finally:
        # Remove the probe route from the live app so it doesn't leak
        # into other tests or `/openapi.json`.
        app.router.routes = [
            r for r in app.router.routes
            if getattr(r, "path", None) != "/__runtime_error_probe__"
        ]

    assert response.status_code == 503
    body = response.json()
    assert body == {"detail": "synthetic failure"}


# ---------------------------------------------------------------------------
# CORS — frontend dev proxy depends on this
# ---------------------------------------------------------------------------


def test_cors_allows_arbitrary_origin_on_preflight():
    """allow_origins=["*"] in main.py is intentional for the workshop.
    The frontend dev server proxies /api -> :8000; production will need
    a real allowlist, and this test should be updated then. For now,
    pin the documented behavior so accidental tightening is loud."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    allow_origin = response.headers.get("access-control-allow-origin")
    # Starlette's CORSMiddleware echoes the origin when allow_credentials=True,
    # which it is here. Either "*" or the echoed origin is acceptable.
    assert allow_origin in ("*", "http://localhost:5173")
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_cors_exposes_origin_header_on_simple_get():
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin in ("*", "http://localhost:5173")


# ---------------------------------------------------------------------------
# OpenAPI surface
# ---------------------------------------------------------------------------


def test_openapi_lists_campaigns_route():
    """Catches accidental un-registration of the campaigns router in main.py."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    assert "/campaigns" in spec["paths"], (
        "GET /campaigns missing from OpenAPI spec — was the router "
        "removed from main.py?"
    )
    assert "get" in spec["paths"]["/campaigns"]


def test_openapi_describes_campaign_response_schema():
    """If CampaignOut changes shape silently, the frontend client breaks.
    Pin the field list at the OpenAPI level so a rename is visible."""
    response = client.get("/openapi.json")
    spec = response.json()

    schemas = spec.get("components", {}).get("schemas", {})
    assert "CampaignOut" in schemas, "CampaignOut schema missing from OpenAPI"

    properties = schemas["CampaignOut"]["properties"]
    for field in (
        "id",
        "campaign_code",
        "name",
        "advertiser",
        "status",
        "objective",
        "start_date",
        "end_date",
        "budget_usd",
        "created_at",
        "updated_at",
    ):
        assert field in properties, f"CampaignOut.{field} missing from OpenAPI"
