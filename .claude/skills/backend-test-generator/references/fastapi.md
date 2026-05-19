# FastAPI + pytest

## Stack signals

- `fastapi` in `pyproject.toml` / `requirements.txt`
- `app = FastAPI(...)` somewhere, usually `app/main.py` or `main.py`
- Routers via `APIRouter` and `app.include_router(...)`
- pytest is the near-universal test framework; `unittest` shows up in older codebases.

## Default toolkit

- **Test framework**: `pytest`
- **HTTP client**: `from fastapi.testclient import TestClient` for sync tests, `httpx.AsyncClient` for async-only flows
- **DB**: SQLAlchemy 2.x with a transactional rollback fixture, or an in-memory SQLite for projects where the DB is incidental
- **Mocks**: `unittest.mock.patch` / `monkeypatch` / `pytest-mock`
- **Time**: `freezegun` if available, otherwise inject a clock

## Where tests live

Standard layouts (use whichever the project already has, or default to the first):

```text
backend/
  tests/
    __init__.py
    conftest.py
    test_<resource>.py
```

`conftest.py` at the `backend/` level usually handles `sys.path` and shared fixtures. Don't create a second `conftest.py` if one already exists with the imports you need — extend the existing one.

## Smallest useful test (route smoke)

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## Dependency overrides

The cleanest way to swap a dependency (DB session, auth, external client) for a test is `app.dependency_overrides`:

```python
from app.main import app
from app.database import get_db

def override_get_db():
    yield FakeSession()

app.dependency_overrides[get_db] = override_get_db
# ... run test ...
app.dependency_overrides.clear()  # or do this in a fixture teardown
```

Prefer this over monkey-patching module-level globals — it's the supported escape hatch and it doesn't leak between tests when paired with a fixture that cleans up.

## DB strategies

In rough order of preference:

1. **Real Postgres + transactional rollback per test.** Fixture starts a transaction, yields a session, rolls back on teardown. Best fidelity. Requires Postgres to be running (often via Supabase, Docker, or testcontainers).
2. **In-memory SQLite for tests** (when the schema is portable). Fast, no infra, but watch for SQLite-specific gotchas (looser type checking, no JSONB, no array types).
3. **Faked repository / session.** Cheap and fast, but can drift from real behavior. Reasonable when the test is really about the handler logic, not the query.

If the project already has a DB strategy, mirror it. Don't introduce a third pattern.

## Async endpoints

If the route is `async def` and uses async DB sessions, prefer `httpx.AsyncClient(app=app, base_url="http://test")` inside an `@pytest.mark.asyncio` test. Set up `pytest-asyncio` if not already configured.

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_route():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/async-resource")
    assert response.status_code == 200
```

## Common patterns

- **403/401 on auth**: `client.get("/protected")` without a token → 401; with a wrong-role token → 403.
- **422 on validation**: send a request body missing a required field; assert 422 and the offending field in the response.
- **404 on missing**: hit `GET /resources/{nonexistent_id}` and assert 404.
- **Idempotent creates**: post the same payload twice; assert the second response is the documented behavior (409, 200 with same id, etc.).

## Project quirk: lazy DB init returning 503

If the project's `database.py` raises `RuntimeError` when `DATABASE_URL` is missing and `main.py` translates it to a 503, a route test should accept *both* 200 and 503:

```python
def test_campaigns_endpoint_exists():
    response = client.get("/campaigns")
    # 200 if DB is up, 503 if DATABASE_URL is unset.
    # Either way, the route is registered and FastAPI handled it.
    assert response.status_code in [200, 503]
```

This is intentional — don't "fix" it. If you see the same pattern (lazy DB, 503 fallback) in the project's existing tests, follow it for new endpoints.

## Running

```bash
uv run pytest                                     # full suite
uv run pytest tests/test_campaigns.py             # one file
uv run pytest tests/test_campaigns.py::test_create_campaign_returns_201  # one test
uv run pytest -k "campaign and not auth"          # name filter
uv run pytest -x                                   # stop on first failure
uv run pytest --lf                                 # rerun last failures
```

If `uv` isn't in use, the same commands work with `pytest` directly inside an activated venv.
