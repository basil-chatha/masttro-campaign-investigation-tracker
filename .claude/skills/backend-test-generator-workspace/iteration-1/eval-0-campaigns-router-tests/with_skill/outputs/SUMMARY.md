# eval-0 with_skill — SUMMARY

(The subagent was prevented from writing this file directly by a project hook, so it's saved here by the orchestrator from the subagent's final report.)

## Stack detected
Python / FastAPI 0.104.1 + pytest 7.4.3 + SQLAlchemy 2.0.23. Detected from `backend/requirements.txt`, `backend/CLAUDE.md` (which states the test command is `uv run pytest`), and the existing `backend/tests/test_health.py` (uses `from fastapi.testclient import TestClient`, module-level `client`, plain `def test_…`).

## References read
- `.claude/skills/backend-test-generator/SKILL.md`
- `.claude/skills/backend-test-generator/references/fastapi.md`
- `.claude/skills/backend-test-generator/references/general.md`

## Files written
- `backend/tests/test_campaigns.py` (within the eval output dir under that relative path)

## What's covered (9 tests)
The campaigns router currently exposes only `GET /campaigns` returning `List[CampaignOut]`. Tests split into two groups:

**Route wiring (real `get_db`, accepts 200 or 503 per the documented lazy-DB contract):**
1. `test_get_campaigns_route_is_registered` — route is mounted; 200 or 503.
2. `test_get_campaigns_with_trailing_slash_is_not_a_separate_route` — `/campaigns/` doesn't 404; redirect or same status.
3. `test_post_campaigns_is_not_allowed` — POST returns 405.

**Handler behavior (overrides `get_db` via `app.dependency_overrides` with a `_FakeSession` so tests run without Postgres):**
4. `test_get_campaigns_returns_empty_list_when_no_rows`
5. `test_get_campaigns_returns_list_of_campaign_out`
6. `test_get_campaigns_returns_all_rows_in_db_order` (no `ORDER BY` in handler; pins current behavior)
7. `test_get_campaigns_serializes_optional_fields_as_null`
8. `test_get_campaigns_serializes_datetimes_as_iso_strings`
9. `test_get_campaigns_response_matches_campaign_out_schema` (uses `CampaignOut.model_fields` as source of truth)

The `override_db` fixture cleans up `app.dependency_overrides` on teardown so tests don't leak.

## Deliberately not covered
- `GET /campaigns/{id}`, `GET /campaigns/{id}/health`, `GET /campaigns/{id}/investigations` — workshop TODOs, not implemented.
- Live Postgres integration — handler tests use `dependency_overrides` instead.
- Pagination/filtering/ordering — not implemented.
- The ORM/framework itself.

## Run command
```bash
cd backend && uv run pytest tests/test_campaigns.py
```
