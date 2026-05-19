"""
Error / edge-case tests for the Campaign Investigation Tracker API.

These tests exercise what happens when clients call endpoints incorrectly
(wrong method, unknown path, malformed query) and verify the project's
documented lazy-DB → 503 fallback contract for routes that depend on a
database session.

Conventions mirrored from `tests/test_health.py`:
- plain `def test_*` functions (no class-based tests)
- `from fastapi.testclient import TestClient` with a module-level client
- `from app.main import app`

Run with:
    uv run pytest backend/tests/test_errors.py
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Wrong HTTP method (405 Method Not Allowed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/campaigns",
    ],
)
def test_post_to_get_only_route_returns_405(path):
    """GET-only routes must reject POST with 405, not 404 or 500."""
    response = client.post(path, json={})
    assert response.status_code == 405


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/campaigns",
    ],
)
def test_delete_on_get_only_route_returns_405(path):
    """GET-only routes must reject DELETE with 405."""
    response = client.delete(path)
    assert response.status_code == 405


def test_put_on_health_returns_405():
    """PUT to a GET-only route should be 405, with an Allow header advertising GET."""
    response = client.put("/health", json={})
    assert response.status_code == 405
    # Starlette/FastAPI sets the Allow header on 405 responses.
    allow = response.headers.get("allow", "")
    assert "GET" in allow.upper()


def test_patch_on_campaigns_returns_405():
    """PATCH on /campaigns is not registered; expect 405 (route exists, method doesn't)."""
    response = client.patch("/campaigns", json={})
    assert response.status_code == 405


# ---------------------------------------------------------------------------
# Unknown routes (404 Not Found)
# ---------------------------------------------------------------------------

def test_unknown_top_level_path_returns_404():
    """A path that was never registered should return 404, not 500."""
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404


def test_typo_of_health_returns_404():
    """Common typo of /health (e.g. /healthz) is not registered — should be 404."""
    response = client.get("/healthz")
    assert response.status_code == 404


def test_campaigns_subpath_not_yet_implemented_returns_404():
    """
    GET /campaigns/{id} is a workshop TODO and not yet wired up.
    Until it's implemented, requesting it should yield a 404.
    When the workshop adds the route, this test will start failing —
    that's a useful signal that the test should be updated alongside.
    """
    response = client.get("/campaigns/some-campaign-id")
    assert response.status_code == 404


def test_investigations_endpoint_not_yet_implemented_returns_404():
    """
    /investigations is a Step 5 TODO; the router isn't registered yet.
    Confirm the API doesn't accidentally serve it.
    """
    response = client.get("/investigations")
    assert response.status_code == 404


def test_ai_runs_endpoint_not_yet_implemented_returns_404():
    """/ai-runs is a Step 12 TODO; ensure it's not silently exposed."""
    response = client.get("/ai-runs")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Lazy-DB → 503 fallback contract
# ---------------------------------------------------------------------------
#
# `app/database.py` raises RuntimeError when DATABASE_URL is missing,
# and `app/main.py` translates that into a 503 JSON response. The
# /campaigns endpoint is the canonical user of this pattern.
#
# We accept *both* 200 and 503 from /campaigns to match the project's
# documented contract (see tests/test_health.py::test_campaigns_endpoint_exists
# and backend/CLAUDE.md). The tests below additionally pin down the 503
# branch by clearing the cached engine and DATABASE_URL so the failure
# path executes deterministically.


def test_campaigns_returns_200_or_503():
    """Project contract: /campaigns is 200 (DB up) or 503 (DB unconfigured)."""
    response = client.get("/campaigns")
    assert response.status_code in (200, 503)


def test_campaigns_503_response_is_json_with_detail(monkeypatch):
    """
    When DATABASE_URL is unset, /campaigns must return a JSON body of the form
    {"detail": "..."} — that's the contract enforced by the RuntimeError handler
    in app/main.py. Verify shape and content-type.
    """
    # Force the lazy-DB failure path: clear the cached engine and unset the env.
    from app import database as db_module

    monkeypatch.setattr(db_module, "_engine", None)
    monkeypatch.setattr(db_module, "_SessionLocal", None)
    monkeypatch.setattr(db_module, "DATABASE_URL", None)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get("/campaigns")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], str)
    # The RuntimeError message in database.py mentions DATABASE_URL — make sure
    # we're not silently swallowing that diagnostic.
    assert "DATABASE_URL" in body["detail"]


def test_runtime_error_handler_translates_to_503(monkeypatch):
    """
    Independent of the DB code, the global RuntimeError exception handler
    registered in app/main.py should turn any unhandled RuntimeError raised
    inside a route into a 503 JSON response.

    We exercise this by overriding get_db with a generator that raises
    RuntimeError before yielding a session — the exact failure mode of
    the lazy DB initializer.
    """
    from app.database import get_db

    def boom():
        raise RuntimeError("simulated DB outage")
        yield  # pragma: no cover — keep this a generator function

    app.dependency_overrides[get_db] = boom
    try:
        # raise_server_exceptions=False lets us see the response Starlette
        # produces from the registered exception handler instead of having
        # TestClient re-raise the exception in the test process.
        with TestClient(app, raise_server_exceptions=False) as isolated_client:
            response = isolated_client.get("/campaigns")
        assert response.status_code == 503
        body = response.json()
        assert body == {"detail": "simulated DB outage"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Misc edge cases on existing routes
# ---------------------------------------------------------------------------

def test_health_ignores_unknown_query_params():
    """Unknown query params on /health must not change behaviour or status."""
    response = client.get("/health?foo=bar&x=1")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_campaigns_with_trailing_slash_does_not_500():
    """
    The router declares /campaigns (no trailing slash). FastAPI / Starlette
    typically issues a redirect for the trailing-slash variant. Either way,
    we should never see a 5xx from the framework layer here — only a
    documented 2xx/3xx/404/503 outcome.
    """
    response = client.get("/campaigns/", follow_redirects=False)
    assert response.status_code < 500
    # Allow the common outcomes: a redirect, the route itself, the lazy-DB
    # 503, or a 404 if redirects are disabled in this FastAPI version.
    assert response.status_code in (200, 307, 308, 404, 503)


def test_options_on_campaigns_is_handled_by_cors():
    """
    CORS middleware (allow_origins=*) should answer OPTIONS preflight
    without hitting the route handler — and therefore without touching
    the database. A 503 here would mean preflight is being routed through
    the DB-bound handler, which is wrong.
    """
    response = client.options(
        "/campaigns",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    # Successful preflight is 200 (or 204 in some configurations).
    assert response.status_code in (200, 204)
    assert response.status_code != 503


def test_root_payload_is_well_formed_json():
    """Sanity: the root route must always return JSON, never crash."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    # Keys promised by app/main.py::root — if any go missing, the frontend
    # client docs page will quietly break.
    assert {"message", "version", "docs"} <= set(body.keys())
