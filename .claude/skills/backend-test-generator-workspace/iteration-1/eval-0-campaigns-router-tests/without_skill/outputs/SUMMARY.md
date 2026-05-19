# Campaigns router test suite

## File added

- backend/tests/test_campaigns.py

## Project conventions followed

- pytest + fastapi.testclient.TestClient, matching backend/tests/test_health.py.
- 'from app.main import app' / 'from app.database import get_db' style imports
  (works because backend/conftest.py adds the backend/ directory to sys.path).
- Honors the lazy DB-init pattern documented in backend/CLAUDE.md: contract
  tests accept either 200 or 503 from the real app, exactly like
  test_campaigns_endpoint_exists in test_health.py.
- No new dependencies. Only uses libraries already pinned in
  backend/requirements.txt (pytest, fastapi, httpx, sqlalchemy, pydantic).

## What is tested

### Layer 1 - contract tests (no DB override)

- test_list_campaigns_route_is_registered: /campaigns returns 200 or 503 (route exists, no 404/500).
- test_list_campaigns_returns_json_list_when_db_available: Response body is a JSON list when DB is reachable; otherwise skipped.
- test_list_campaigns_503_payload_shape: When DB is missing, the 503 has a 'detail' mentioning DATABASE_URL (came from the RuntimeError handler).
- test_campaigns_router_has_correct_prefix_and_tag: /campaigns is registered and the OpenAPI operation is tagged 'campaigns'.
- test_unimplemented_campaign_detail_route_returns_404: /campaigns/{id} (workshop TODO) currently 404s - guard against silent regressions.
- test_unimplemented_campaign_health_route_returns_404: Same guard for /campaigns/{id}/health.

### Layer 2 - functional tests with in-memory SQLite

Uses app.dependency_overrides[get_db] plus an in-memory SQLite engine populated from Base.metadata.create_all. The Campaign model only uses column types SQLite supports, so the real router can be exercised end-to-end without Postgres.

- test_list_campaigns_returns_empty_list_when_no_rows: Empty table -> 200 [].
- test_list_campaigns_returns_seeded_rows: Two seeded rows are returned with all CampaignOut fields populated.
- test_list_campaigns_serializes_optional_nullable_fields: Optional fields (channel, owner_name, region) round-trip as None.
- test_list_campaigns_serializes_datetimes_as_iso_strings: Datetime fields serialize as ISO-8601 strings parseable by datetime.fromisoformat.
- test_list_campaigns_does_not_accept_post: POST /campaigns -> 405 (only GET is registered today).
- test_list_campaigns_trailing_slash_behavior: /campaigns/ either returns 200 or 307-redirects (does not 404).

## What is intentionally skipped

- GET /campaigns/{id} and GET /campaigns/{id}/health - not yet implemented (TODOs in routers/campaigns.py). Covered only by 'currently 404s' guard tests above.
- GET /campaigns/{id}/investigations - depends on the Investigation model which is also TODO.
- Real Postgres / Supabase seed-data tests - out of scope; the in-memory SQLite override is sufficient for unit-level coverage of the current router code.
- Auth / permission assertions - none are implemented in the API yet.

## How to run

From the backend/ directory:

    uv run pytest tests/test_campaigns.py -v

Per task constraints, the suite was NOT executed.
