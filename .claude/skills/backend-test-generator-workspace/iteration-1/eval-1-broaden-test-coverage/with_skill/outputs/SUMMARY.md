# eval-1 with_skill — SUMMARY

(Saved by orchestrator from subagent's final report; agent was hook-blocked from writing this file directly.)

## Stack detected
- Python 3.10+ / FastAPI 0.104, SQLAlchemy 2.x, pytest 7.4, `fastapi.testclient.TestClient`.
- Lazy-engine DB strategy. Test runner per `backend/CLAUDE.md`: `uv run pytest`.

## References read
- `.claude/skills/backend-test-generator/SKILL.md`
- `.claude/skills/backend-test-generator/references/fastapi.md`
- `.claude/skills/backend-test-generator/references/general.md`
- `backend/CLAUDE.md`

## Existing coverage (before)
6 smoke tests in `test_health.py` covering `/health`, `/`, `/campaigns` (200/503), `/docs`. Handler logic, serialization, error contracts, CORS, the `RuntimeError → 503` handler, and the lazy-DB module itself were all untested.

## Files added (16 new tests across 3 files)

### `test_campaigns.py` — 8 tests
Uses `app.dependency_overrides[get_db]` with a `_FakeSession` to exercise the handler + serializer end-to-end without a real DB.
1. empty list when no rows
2. serialized rows
3. response shape (pinned field names)
4. optional fields serialize as `null`
5. RuntimeError → 503 contract
6. POST → 405
7. unknown route → 404
8. trailing-slash behavior

### `test_app_contract.py` — 5 tests
1. RuntimeError handler translates arbitrary RuntimeErrors to 503 (synthetic route + cleanup)
2. CORS preflight allows arbitrary origin
3. CORS exposes origin on simple GET
4. OpenAPI lists `/campaigns`
5. OpenAPI describes `CampaignOut`

### `test_database.py` — 3 tests
Direct unit tests on lazy-init via `monkeypatch` + `importlib.reload`.
1. `get_db` raises RuntimeError when DATABASE_URL missing
2. `_init_db` idempotent (sqlite memory)
3. `get_db` yields session and closes it

## Deferred
- TODO routes (investigations, ai-runs, campaign detail) — not implemented yet
- Real Postgres integration
- Stricter CORS allowlist (workshop uses `*`)
- `httpx.AsyncClient` (all routes sync)
- ORM / Pydantic stand-alone tests (no custom logic)

## Pytest command
```bash
cd backend && uv run pytest
```
