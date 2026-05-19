# eval-1 without_skill — SUMMARY

(Saved by the orchestrator from the subagent's final report; subagent was hook-blocked from writing .md files.)

## Existing state

`backend/tests/` had a single file, `test_health.py` (6 tests):
- 2 health-endpoint smoke tests, 2 root-endpoint smoke tests, 1 `/docs` smoke test
- 1 `/campaigns` route-exists test that accepts **either 200 or 503**
- 4 TODO comments for investigation tests against routes that don't exist yet

## What was added

### `test_database.py` — lazy-DB pattern (regression guards)
- `_init_db()` raises `RuntimeError` without `DATABASE_URL`
- `get_db()` surfaces the same error on first iteration
- Importing `app.database` does NOT eagerly construct the engine
- Engine + session built lazily on first call; `_init_db()` is idempotent
- `get_db()` yields a `Session` and closes it cleanly
Uses `monkeypatch` + `importlib.reload` for env isolation, in-memory SQLite for success branch.

### `test_campaigns.py` — real DB exercise
Wires SQLite in-memory via `app.dependency_overrides[get_db]`, seeds `Campaign` rows.
- Empty DB returns `[]`
- Seeded row round-trips through `CampaignOut`
- Multiple rows
- Nullable optional fields (`channel`, `owner_name`, `region`) serialize to `null`

### `test_app_contract.py` — cross-cutting invariants
- 503 contract on `/campaigns` when unconfigured: status + JSON body shape
- 503 response is `application/json` not HTML
- CORS preflight + simple GET origin echoing
- `/openapi.json` served and well-formed
- `/campaigns` registered in OpenAPI `paths`
- Tag is `campaigns`
- `CampaignOut` in `components.schemas`
- `/health` works regardless of DB state

### `test_schemas.py` — `CampaignOut` unit tests
- ORM-attribute validation (`from_attributes=True`)
- Pinned serialized field set
- Optional fields accept `None`
- Missing required field raises `ValidationError`
- Non-numeric `budget_usd` raises `ValidationError`
- Pinned required fields in JSON schema

## Deferred

- Investigations / AI runs tests (TODO stubs not implemented)
- Real Postgres integration tests
- Status-transition state machine tests
- End-to-end frontend↔backend tests

## Pytest command

```bash
cd backend && uv run pytest
```
