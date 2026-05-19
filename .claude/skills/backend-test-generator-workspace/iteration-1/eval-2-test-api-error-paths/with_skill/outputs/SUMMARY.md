# Backend Error-Path Test Suite — Summary

## Stack detected

- Language / framework: Python 3.10+ / FastAPI 0.104.1 (backend/requirements.txt)
- Test framework: pytest 7.4.3 (already in requirements; existing backend/tests/test_health.py uses plain def test_* functions with fastapi.testclient.TestClient)
- HTTP client in tests: fastapi.testclient.TestClient
- Database: lazy SQLAlchemy 2.x (Postgres via Supabase), engine built on first get_db() call. Missing DATABASE_URL -> RuntimeError -> translated to HTTP 503 by the global handler in app/main.py.
- Test layout: backend/tests/test_*.py, with backend/conftest.py adding backend/ to sys.path.
- Test command: uv run pytest (per backend/CLAUDE.md)

## Reference files read

- .claude/skills/backend-test-generator/SKILL.md (workflow)
- .claude/skills/backend-test-generator/references/fastapi.md (FastAPI specifics, especially the lazy-DB -> 503 contract section)
- .claude/skills/backend-test-generator/references/general.md (boundary principle, naming, error-case checklist)

I also surveyed the actual project surface area before writing tests:

- backend/app/main.py — registered routes (/, /health, /campaigns), CORS, RuntimeError -> 503 handler, TODO routers (investigations, ai_runs) NOT yet registered.
- backend/app/routers/campaigns.py — only GET /campaigns is implemented; /campaigns/{id}, /campaigns/{id}/health, /campaigns/{id}/investigations are TODOs.
- backend/app/database.py — confirmed the RuntimeError message format (mentions DATABASE_URL) and the lazy _engine/_SessionLocal cache that needs to be cleared to force the 503 branch deterministically.
- backend/tests/test_health.py — copied conventions (module-level client, function-style tests, assert status_code in [200, 503] on /campaigns).

## What is covered

All tests live in backend/tests/test_errors.py.

### Wrong HTTP method -> 405
- POST against /, /health, /campaigns (parametrized)
- DELETE against /, /health, /campaigns (parametrized)
- PUT /health — also asserts the Allow header advertises GET
- PATCH /campaigns

These pin down that registered routes reject unsupported verbs with 405 (not 404 or 500).

### Unknown route -> 404
- /this-route-does-not-exist
- /healthz (common alternative health probe)
- /campaigns/{id} — explicitly NOT yet implemented; test will start failing when Step 4 lands.
- /investigations — Step 5 TODO; verify it is not accidentally exposed.
- /ai-runs — Step 12 TODO; same reasoning.

### Lazy-DB -> 503 contract (the headline)
- test_campaigns_returns_200_or_503 — preserves the project contract that /campaigns may be either, depending on DATABASE_URL.
- test_campaigns_503_response_is_json_with_detail — pins down the 503 branch deterministically by clearing the cached _engine/_SessionLocal and unsetting DATABASE_URL via monkeypatch. Asserts JSON shape ({"detail": "..."}), content-type, and that the diagnostic message mentions DATABASE_URL.
- test_runtime_error_handler_translates_to_503 — exercises the global RuntimeError handler independently of the DB code, by overriding the get_db dependency with a generator that raises RuntimeError. Uses TestClient(app, raise_server_exceptions=False). Cleans up app.dependency_overrides in a try/finally.

### Misc edge cases
- test_health_ignores_unknown_query_params — unknown query string does not change /health behavior.
- test_campaigns_with_trailing_slash_does_not_500 — /campaigns/ yields a documented status (200/307/308/404/503), never a 5xx from the framework.
- test_options_on_campaigns_is_handled_by_cors — CORS preflight returns 200/204 and explicitly NOT 503.
- test_root_payload_is_well_formed_json — sanity check that / always returns JSON with the documented keys (message, version, docs).

## What I deliberately skipped

- /campaigns/{id} 404 semantics — the route does not exist yet. The placeholder test_campaigns_subpath_not_yet_implemented_returns_404 documents current state and will flip when implemented.
- 422 validation tests — none of the currently-registered routes accept a request body or validated parameter.
- Auth / authorization (401, 403) — there is no auth layer in this skeleton.
- Rate limiting / throttling — not configured.
- Real Postgres rollback fixtures — not needed for this slice; existing tests do not use them, and the error-path tests run without a database.
- CORS specifics like exact Access-Control-* headers — allow_origins=["*"] is workshop-only.
- Async tests — all routes are sync def, so the sync TestClient is the right boundary.

## How to run

From the project root:

    cd backend
    uv run pytest tests/test_errors.py -v

Or run the full suite (includes the existing test_health.py):

    cd backend
    uv run pytest -v

If uv is not on PATH, the same commands work with a plain pytest inside an activated venv created from backend/requirements.txt.

## File deliverables

- backend/tests/test_errors.py — 17 tests across wrong-method, unknown-route, lazy-DB -> 503, and misc edge cases. Mirrors the existing tests/test_health.py conventions.
- No new fixtures or conftest.py changes — the existing backend/conftest.py already adds the right sys.path entry, and monkeypatch from pytest-stdlib is sufficient for the lazy-DB tests.
