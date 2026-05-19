# Backend error-path tests — summary

## What this adds

A single new file: backend/tests/test_errors.py.

It mirrors the project's existing test layout (FastAPI TestClient against
app.main:app, no DB-bound fixtures), so it works under the project's
existing pytest setup with no new dependencies, no new fixtures in
conftest.py, and no env changes.

## Pytest command

From the backend/ directory:

    uv run pytest tests/test_errors.py
    # or a single class:
    uv run pytest tests/test_errors.py::TestLazyDbFallback

## Error paths covered

- TestUnknownRoutes — Top-level / nested unknown routes 404 with JSON body.
  Parametrized list of not-yet-implemented workshop routes (campaign detail,
  campaign health, campaign investigations, /investigations, /ai-runs)
  currently 404 (or 307 for trailing-slash redirect).

- TestWrongMethod — POST/PUT/PATCH/DELETE on /health, /, and /campaigns all
  return 405. The 405 response includes an Allow: GET header per RFC 7231.

- TestCors — OPTIONS preflight on /campaigns from a browser-style origin
  returns 200 with Access-Control-Allow-Origin.

- TestLazyDbFallback — The core "do not break this" behavior from
  backend/CLAUDE.md. With app.database monkeypatched into an unconfigured
  state (_engine=None, _SessionLocal=None, DATABASE_URL=None):
    * GET /campaigns -> 503 JSON whose detail mentions DATABASE_URL
    * GET /health, /, /docs, /openapi.json all keep returning 200
  Also dynamically registers a throwaway router that raises RuntimeError to
  prove the global handler in main.py converts it into a 503 (not a 500
  traceback).

- TestMalformedInput — The current surface declares no validated input, so
  there is no real 422 case to assert today. Instead, this class locks in:
  unknown query params on /health are ignored (200), junk query params on
  /campaigns never 500 (only 200/503), and a 2000-char garbage path returns
  a clean 404. Comments mark these as the slot where future Step-5
  (POST /investigations) 422 cases should land.

- TestErrorResponseShape — 404 and 405 bodies are JSON dicts with a detail
  field, matching FastAPI default contract.

## What was deliberately skipped

- Real 422 / Pydantic-validation cases. The current API has no endpoint
  that declares a request body or typed path/query parameter, so there is
  no input that FastAPI would reject with 422. The workshop TODOs (Step 5
  POST /investigations, Step 10 PATCH /investigations/{id}/status) are the
  natural home for those tests; TestMalformedInput is structured so they
  drop in next to the existing placeholders.

- Real 404 resource-not-found cases (e.g. GET /campaigns/{unknown_id}).
  That endpoint is itself a Step-4 TODO and not registered yet. The
  parametrized list in TestUnknownRoutes already locks in that the route
  currently 404s; when Step 4 lands, those entries should flip into proper
  "missing resource" tests.

- Authentication / authorization errors (401, 403). The current API has no
  auth layer.

- DB-integration error cases (e.g. simulating a Postgres connection drop
  mid-query). Out of scope for "right HTTP responses when things go wrong"
  at the API surface, and would require a real DB or heavier monkeypatching
  of SQLAlchemy.

- Modifying conftest.py. The existing conftest.py already adds backend/ to
  sys.path; nothing else is needed for these tests.

## Files written

- backend/tests/test_errors.py — the test module described above.

(Per task constraints, written into the eval output directory only — the
project tree was not touched. To use them, copy the file into the project
backend/tests/ directory.)
