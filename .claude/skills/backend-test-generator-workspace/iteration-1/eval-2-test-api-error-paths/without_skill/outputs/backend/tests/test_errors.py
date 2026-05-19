"""
Error / edge-case tests for the Campaign Investigation Tracker API.

These tests verify that the FastAPI app returns the *right* HTTP responses
when callers do something wrong:

  * 404 for unknown routes
  * 405 for the wrong HTTP method on a known route
  * 422 for malformed query parameters
  * 503 for the lazy-DB fallback (the RuntimeError handler in main.py)
  * Healthy endpoints (/health, /, /docs, /openapi.json) keep working
    even when the database is unreachable.

Runnable with the project's existing pytest setup:

    cd backend
    uv run pytest tests/test_errors.py
"""
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# 404 — unknown routes
# ---------------------------------------------------------------------------

class TestUnknownRoutes:
    """Routes that don't exist should cleanly return 404, not 500."""

    def test_unknown_top_level_route_returns_404(self):
        response = client.get("/this-route-does-not-exist")
        assert response.status_code == 404

    def test_unknown_nested_route_returns_404(self):
        response = client.get("/api/v99/totally/made/up")
        assert response.status_code == 404

    def test_404_response_is_json(self):
        response = client.get("/no-such-endpoint")
        assert response.status_code == 404
        # FastAPI's default 404 body is JSON with a `detail` field.
        assert response.headers["content-type"].startswith("application/json")
        assert "detail" in response.json()

    @pytest.mark.parametrize(
        "path",
        [
            "/campaigns/",  # currently the route is /campaigns (no trailing slash)
            "/campaigns/xyz",  # campaign-detail endpoint is a TODO
            "/campaigns/xyz/health",  # also a TODO
            "/campaigns/xyz/investigations",  # also a TODO
            "/investigations",  # router not registered yet (Step 5 TODO)
            "/investigations/abc",
            "/ai-runs",  # router not registered yet (Step 12 TODO)
        ],
    )
    def test_unimplemented_workshop_routes_return_404(self, path):
        """
        Routes that the workshop *plans* to add (Step 4 / 5 / 12 TODOs) should
        not exist yet. They should 404, not 500.

        These tests intentionally lock in the current pre-workshop behavior so
        that when the routes are implemented, the test fails loudly and a
        positive-path test should be added in its place.
        """
        response = client.get(path)
        # 307 is what FastAPI returns when a trailing-slash mismatch redirects.
        # Anything other than 404 / 307 means the route is now live.
        assert response.status_code in (404, 307), (
            f"Expected 404 (or 307 redirect) for unimplemented {path}, "
            f"got {response.status_code}. If you just implemented this route, "
            "replace this test with a real assertion."
        )


# ---------------------------------------------------------------------------
# 405 — wrong HTTP method
# ---------------------------------------------------------------------------

class TestWrongMethod:
    """Sending the wrong verb on a known route should yield 405."""

    @pytest.mark.parametrize(
        "method",
        ["post", "put", "patch", "delete"],
    )
    def test_health_rejects_non_get_methods(self, method):
        response = getattr(client, method)("/health")
        assert response.status_code == 405

    @pytest.mark.parametrize(
        "method",
        ["post", "put", "patch", "delete"],
    )
    def test_root_rejects_non_get_methods(self, method):
        response = getattr(client, method)("/")
        assert response.status_code == 405

    @pytest.mark.parametrize(
        "method",
        ["post", "put", "patch", "delete"],
    )
    def test_campaigns_rejects_non_get_methods(self, method):
        # /campaigns currently only supports GET. Anything else must be 405.
        response = getattr(client, method)("/campaigns")
        assert response.status_code == 405

    def test_405_includes_allow_header(self):
        response = client.post("/health")
        assert response.status_code == 405
        # Per RFC 7231, a 405 SHOULD include an Allow header. FastAPI/Starlette
        # populates this; assert it lists GET so clients can self-correct.
        allow = response.headers.get("allow", "")
        assert "GET" in allow.upper()


# ---------------------------------------------------------------------------
# CORS — preflight should still succeed even on unknown routes
# ---------------------------------------------------------------------------

class TestCors:
    def test_cors_preflight_on_known_route(self):
        response = client.options(
            "/campaigns",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # Starlette's CORSMiddleware short-circuits OPTIONS preflight to 200.
        assert response.status_code == 200
        assert "access-control-allow-origin" in {
            k.lower() for k in response.headers.keys()
        }


# ---------------------------------------------------------------------------
# 503 — lazy DB fallback (the RuntimeError → JSONResponse handler in main.py)
# ---------------------------------------------------------------------------

class TestLazyDbFallback:
    """
    When the DB isn't configured, hitting a DB-backed endpoint should yield
    a clean 503 with a JSON body — never a 500 traceback.

    We force this state regardless of whether DATABASE_URL is set in the test
    environment by monkeypatching app.database to behave as if it weren't.
    """

    def _force_db_unconfigured(self, monkeypatch):
        # Reset the cached engine/session so _init_db() takes the failure path.
        monkeypatch.setattr(database, "_engine", None, raising=False)
        monkeypatch.setattr(database, "_SessionLocal", None, raising=False)
        # Pretend DATABASE_URL is missing.
        monkeypatch.setattr(database, "DATABASE_URL", None, raising=False)

    def test_campaigns_returns_503_when_db_unconfigured(self, monkeypatch):
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/campaigns")
        assert response.status_code == 503

    def test_503_body_is_json_with_detail(self, monkeypatch):
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/campaigns")
        assert response.status_code == 503
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert "detail" in body
        # The RuntimeError message in database.py mentions DATABASE_URL.
        assert "DATABASE_URL" in body["detail"]

    def test_health_still_works_when_db_unconfigured(self, monkeypatch):
        """The whole point of the lazy pattern: /health must not need a DB."""
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_still_works_when_db_unconfigured(self, monkeypatch):
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_still_works_when_db_unconfigured(self, monkeypatch):
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_still_works_when_db_unconfigured(self, monkeypatch):
        self._force_db_unconfigured(monkeypatch)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        body = response.json()
        # Schema describes the routes that *are* registered today.
        assert "paths" in body
        assert "/health" in body["paths"]
        assert "/campaigns" in body["paths"]

    def test_runtime_error_handler_converts_to_503(self, monkeypatch):
        """
        Direct sanity check on main.py's RuntimeError exception handler:
        any router that raises RuntimeError should end up as a 503 JSON body,
        not a 500 traceback.
        """
        from fastapi import APIRouter

        boom = APIRouter()

        @boom.get("/__test_boom")
        def _boom():
            raise RuntimeError("manual boom for test")

        app.include_router(boom)
        try:
            response = client.get("/__test_boom")
            assert response.status_code == 503
            assert response.json()["detail"] == "manual boom for test"
        finally:
            # Best-effort cleanup so this synthetic route doesn't leak into
            # other tests in the same session.
            app.router.routes = [
                r for r in app.router.routes
                if getattr(r, "path", None) != "/__test_boom"
            ]


# ---------------------------------------------------------------------------
# 422 — malformed input
# ---------------------------------------------------------------------------

class TestMalformedInput:
    """
    The current API surface (only GET /campaigns, /health, /, /docs) doesn't
    declare any path/query/body parameters with validation. So there is no
    422-producing input today.

    These tests are placeholders that lock that fact in: if a future endpoint
    starts accepting validated input (e.g. POST /investigations from Step 5),
    the workshop should add real 422 cases below. Until then we just confirm
    that extra/garbage query strings on existing endpoints are tolerated.
    """

    def test_unknown_query_params_are_ignored(self):
        # FastAPI ignores unknown query params on routes that declare none.
        response = client.get("/health?foo=bar&baz=qux")
        assert response.status_code == 200

    def test_garbage_query_params_on_campaigns_dont_500(self):
        # /campaigns has no query params; junk shouldn't blow up the handler.
        response = client.get("/campaigns?limit=abc&offset=-1")
        # Either 200 (DB up) or 503 (DB down) — but never 500.
        assert response.status_code in (200, 503)

    def test_extremely_long_path_returns_404_not_500(self):
        # Defensive: a very long unknown path should still be a clean 404.
        long_path = "/" + ("a" * 2000)
        response = client.get(long_path)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Content-type / response-shape sanity for error responses
# ---------------------------------------------------------------------------

class TestErrorResponseShape:
    def test_404_has_detail_field(self):
        body = client.get("/nope").json()
        assert isinstance(body, dict)
        assert "detail" in body

    def test_405_has_detail_field(self):
        body = client.post("/health").json()
        assert isinstance(body, dict)
        assert "detail" in body
