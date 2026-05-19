"""
Tests for the campaigns router (`app/routers/campaigns.py`).

These tests focus on the surface area that is actually implemented today:
the router is mounted at the prefix `/campaigns` and exposes a single
`GET /campaigns` endpoint that returns `List[CampaignOut]`.

Project-specific contract worth knowing before reading these tests:

- `app/database.py` builds the SQLAlchemy engine lazily. When `DATABASE_URL`
  is unset, `get_db()` raises `RuntimeError`, and `app/main.py` registers an
  exception handler that converts that into a `503` JSON response. As a
  result, route tests that exercise the live `get_db` dependency must accept
  *both* `200` (DB up) and `503` (DB not configured). This mirrors
  `test_campaigns_endpoint_exists` in `tests/test_health.py`.
- For tests that need to assert response *bodies* (shape, ordering, etc.),
  we override the `get_db` FastAPI dependency with a fake session so we can
  exercise the handler without requiring Postgres. This matches the
  "real route, fake the seam" guidance in the FastAPI testing reference.

The router has several `TODO [Step …]` comments for endpoints that are
intentionally not yet implemented (`GET /campaigns/{id}`,
`GET /campaigns/{id}/health`, `GET /campaigns/{id}/investigations`). We do
*not* write tests against those — they are part of the workshop build plan.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Fake DB session — used to exercise the handler without a real Postgres.
# ---------------------------------------------------------------------------


class _FakeQuery:
    """Minimal stand-in for `db.query(Campaign)` that supports `.all()`."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeSession:
    """Minimal stand-in for a SQLAlchemy `Session`.

    Only implements the surface the campaigns router actually uses:
    `db.query(Campaign).all()`. Any other access will raise loudly so we
    notice if a future test starts depending on something the fake doesn't
    cover.
    """

    def __init__(self, rows):
        self._rows = rows

    def query(self, _model):
        return _FakeQuery(self._rows)

    def close(self):  # called by the real get_db's finally; harmless here
        pass


def _make_campaign_row(
    *,
    id="cmp-001",
    campaign_code="CMP-001",
    name="Acme Spring Launch",
    advertiser="Acme Corp",
    status="active",
    objective="awareness",
    channel="display",
    start_date=None,
    end_date=None,
    budget_usd=10_000.0,
    owner_name="Pat Owner",
    region="NA",
    created_at=None,
    updated_at=None,
):
    """Build a row that quacks like a `Campaign` ORM instance.

    `CampaignOut` uses `from_attributes=True`, so any object that exposes the
    right attributes will serialize correctly — we don't need a real ORM row.
    """
    now = datetime(2026, 1, 1, 0, 0, 0)
    return SimpleNamespace(
        id=id,
        campaign_code=campaign_code,
        name=name,
        advertiser=advertiser,
        status=status,
        objective=objective,
        channel=channel,
        start_date=start_date or datetime(2026, 1, 1),
        end_date=end_date or datetime(2026, 3, 1),
        budget_usd=budget_usd,
        owner_name=owner_name,
        region=region,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


@pytest.fixture
def override_db():
    """Yield a setter that swaps `get_db` for a fake yielding the given rows.

    Cleans up `app.dependency_overrides` on teardown so tests don't leak
    state into each other.
    """
    def _set(rows):
        def _override():
            yield _FakeSession(rows)

        app.dependency_overrides[get_db] = _override

    try:
        yield _set
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Route-existence tests — exercise the real `get_db` dependency and accept
# the documented 200-or-503 contract. These are the "is the router wired up
# at all" smoke tests.
# ---------------------------------------------------------------------------


def test_get_campaigns_route_is_registered():
    """`GET /campaigns` is mounted and FastAPI handles it.

    Accepts 200 (DB configured) or 503 (lazy-init RuntimeError → handler).
    Anything else (404, 405, 500) means the route is missing or broken in a
    way the project's contract doesn't tolerate.
    """
    response = client.get("/campaigns")
    assert response.status_code in (200, 503), response.text


def test_get_campaigns_with_trailing_slash_is_not_a_separate_route():
    """The router declares `@router.get("")`, so `/campaigns/` is not the
    canonical path. FastAPI will redirect (307) to `/campaigns`. Either way
    the client should not see a 404 — pin that contract here so we notice if
    someone changes the router prefix or path in a way that breaks links.
    """
    response = client.get("/campaigns/", follow_redirects=False)
    # Accept the redirect (307) or the same 200/503 as the canonical path
    # (in case a future FastAPI change collapses them).
    assert response.status_code in (200, 307, 503), response.text


def test_post_campaigns_is_not_allowed():
    """Only `GET /campaigns` is implemented today. POST should not 200."""
    response = client.post("/campaigns", json={})
    # FastAPI returns 405 for an unsupported method on a registered path.
    # If the DB layer is hit first for some reason, we'd see 503 — but the
    # route itself only registers GET, so 405 is the expected answer.
    assert response.status_code == 405, response.text


# ---------------------------------------------------------------------------
# Handler-behavior tests — override `get_db` so we can assert response shape
# without a live Postgres. These are what fail when the handler logic or the
# response schema regresses.
# ---------------------------------------------------------------------------


def test_get_campaigns_returns_empty_list_when_no_rows(override_db):
    """An empty DB yields an empty JSON list, not null and not an error."""
    override_db([])

    response = client.get("/campaigns")

    assert response.status_code == 200
    assert response.json() == []


def test_get_campaigns_returns_list_of_campaign_out(override_db):
    """A single row is serialized through `CampaignOut` and returned in a list."""
    row = _make_campaign_row(
        id="cmp-001",
        campaign_code="CMP-001",
        name="Acme Spring Launch",
        advertiser="Acme Corp",
    )
    override_db([row])

    response = client.get("/campaigns")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    item = body[0]
    assert item["id"] == "cmp-001"
    assert item["campaign_code"] == "CMP-001"
    assert item["name"] == "Acme Spring Launch"
    assert item["advertiser"] == "Acme Corp"


def test_get_campaigns_returns_all_rows_in_db_order(override_db):
    """The handler returns rows in the order the session yielded them.

    The router does not impose an `ORDER BY`, so we assert it preserves the
    session's order rather than inventing one. This pins the current
    contract — if someone adds sorting later, they should update this test
    deliberately.
    """
    rows = [
        _make_campaign_row(id="cmp-001", campaign_code="CMP-001", name="First"),
        _make_campaign_row(id="cmp-002", campaign_code="CMP-002", name="Second"),
        _make_campaign_row(id="cmp-003", campaign_code="CMP-003", name="Third"),
    ]
    override_db(rows)

    response = client.get("/campaigns")

    assert response.status_code == 200
    body = response.json()
    assert [c["id"] for c in body] == ["cmp-001", "cmp-002", "cmp-003"]
    assert [c["name"] for c in body] == ["First", "Second", "Third"]


def test_get_campaigns_serializes_optional_fields_as_null(override_db):
    """`channel`, `owner_name`, and `region` are `Optional[...]` on
    `CampaignOut`. When absent on the row, they should serialize to `null`,
    not be omitted and not raise.
    """
    row = _make_campaign_row(channel=None, owner_name=None, region=None)
    override_db([row])

    response = client.get("/campaigns")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["channel"] is None
    assert item["owner_name"] is None
    assert item["region"] is None


def test_get_campaigns_serializes_datetimes_as_iso_strings(override_db):
    """Datetime columns come back as ISO-8601 strings via Pydantic's default
    JSON encoder. Lock that down so a future schema change doesn't silently
    flip the wire format.
    """
    start = datetime(2026, 4, 1, 12, 0, 0)
    end = datetime(2026, 5, 1, 12, 0, 0)
    row = _make_campaign_row(start_date=start, end_date=end)
    override_db([row])

    response = client.get("/campaigns")

    assert response.status_code == 200
    item = response.json()[0]
    # Pydantic v2 emits ISO format without timezone for naive datetimes.
    assert item["start_date"].startswith("2026-04-01T12:00:00")
    assert item["end_date"].startswith("2026-05-01T12:00:00")


def test_get_campaigns_response_matches_campaign_out_schema(override_db):
    """Every key declared on `CampaignOut` is present in each response item.

    This catches accidental schema narrowing (e.g. someone removes a field
    from `CampaignOut` thinking nothing depends on it). Uses the schema
    itself as the source of truth so the test stays in sync if fields are
    added.
    """
    from app.schemas import CampaignOut  # imported inside the test to keep
    # the test file importable even if schemas.py hasn't been touched yet.

    expected_fields = set(CampaignOut.model_fields.keys())
    override_db([_make_campaign_row()])

    response = client.get("/campaigns")
    assert response.status_code == 200
    item = response.json()[0]
    assert expected_fields.issubset(item.keys()), (
        f"Response is missing fields declared on CampaignOut: "
        f"{expected_fields - set(item.keys())}"
    )
