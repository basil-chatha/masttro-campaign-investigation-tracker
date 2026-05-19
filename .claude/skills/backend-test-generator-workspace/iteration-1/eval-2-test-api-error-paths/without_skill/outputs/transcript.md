# Transcript

Steps taken to generate the error-path test suite.

1. Inspected project layout under backend/:
   - backend/app/main.py (FastAPI app, RuntimeError->503 handler, /health, /, router include)
   - backend/app/database.py (lazy _init_db, raises RuntimeError when DATABASE_URL missing)
   - backend/app/routers/campaigns.py (only GET /campaigns is live; detail/health/investigations are TODOs)
   - backend/app/models.py and schemas.py (only Campaign + CampaignHealth + CampaignOut mapped today; other resources are TODOs)
   - backend/tests/test_health.py (existing pattern: FastAPI TestClient, no fixtures, accepts 200 or 503 on /campaigns)
   - backend/conftest.py (just inserts backend/ on sys.path)
   - backend/requirements.txt (fastapi 0.104.1, pytest 7.4.3, httpx, sqlalchemy 2.0.23, etc.)

2. Cross-checked backend/CLAUDE.md for the "lazy DB pattern - do not break this"
   constraint. Confirmed the core invariants the new tests should lock in:
   - /health and /docs must work without a database
   - DB-backed routes must return 503 (not 500) when DATABASE_URL is missing
   - The 503 must come through main.py exception handler with a JSON detail body

3. Identified the live HTTP surface today: GET /, GET /health, GET /campaigns,
   plus /docs and /openapi.json. Everything else (campaign detail,
   investigations, ai-runs) is intentionally a workshop TODO.

4. Designed the test classes:
   - TestUnknownRoutes (404 on unknown / unimplemented routes)
   - TestWrongMethod (405 on POST/PUT/PATCH/DELETE against GET-only routes,
     plus Allow header check)
   - TestCors (OPTIONS preflight succeeds)
   - TestLazyDbFallback (monkeypatch app.database to force RuntimeError,
     assert 503 JSON; assert /health /docs /openapi.json still 200; plus a
     synthetic router that raises RuntimeError to directly exercise the
     handler)
   - TestMalformedInput (no real 422 cases yet; lock in that junk query
     params do not 500, leave breadcrumbs for Step 5/10 TODOs)
   - TestErrorResponseShape (detail field on 404/405)

5. Wrote backend/tests/test_errors.py into the eval output tree at the same
   relative path it would take inside the project. Did not touch the actual
   project tree.

6. Wrote SUMMARY.md and this transcript.md alongside the test file.

7. Did not run pytest, did not install packages, did not commit.
