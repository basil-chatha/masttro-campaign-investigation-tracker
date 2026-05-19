"""
Tests for the campaigns router.

These tests exercise the /campaigns endpoint with a stubbed database
session via FastAPI's `app.dependency_overrides`, so they don't need
Postgres to run. The goal is to verify:

  - the handler actually queries Campaign and returns rows,
  - CampaignOut serialization works (required + optional fields),
  - the route behaves correctly under wrong methods / unknown ids,
  - a database-layer RuntimeError is translated to a 503 by the
    global exception handler in main.py.

The existing `test_campaigns_endpoint_exists` in test_health.py is a
smoke test that accepts both 200 and 503 — that contract is intentional
and is preserved here. These tests pin down the 200-path behavior.
"""
from datetime import datetime
from typing import List

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Campaign


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_campaign(**overrides) -> Campaign:
    """Build a Campaign ORM instance with sensible defaults.

    We construct a real Campaign so CampaignOut.model_validate (via
    `from_attributes=True`) hits the same code path as production.
    """
    defaults = dict(
        id="cmp_001",
        campaign_code="CMP-001",
        name="Spring Launch",
        advertiser="Acme Corp",
        status="active",
        objective="awareness",
        channel="ctv",
        start_date=datetime(2026, 1, 1, 0, 0, 0),
        end_date=datetime(2026, 3, 31, 0, 0, 0),
        budget_usd=100000.0,
        owner_name="Jane Doe",
        region="NA",
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=datetime(2026, 1, 2, 0, 0, 0),
    )
    defaults.update(overrides)
    return Campaign(**defaults)


class _FakeQuery:
    def __init__(self, rows: List[Campaign]):
        self._rows = rows

    def all(self) -> List[Campaign]:
        return list(self._rows)


class _FakeSession:
    """Minimal stand-in for sqlalchemy.orm.Session.

    The campaigns router only calls `db.query(Campaign).all()`. We mirror
    that surface and nothing more so the test fails loudly if the handler
    starts using something else (filter, get, etc.) — at which point the
    test should be updated to reflect the new contract.
    """

    def __init__(self, rows: List[Campaign]):
        self._rows = rows

    def query(self, model):
        assert model is Campaign, f"unexpected model queried: {model!r}"
        return _FakeQuery(self._rows)

    def close(self):
        pass


@pytest.fixture
def override_db():
    """Yield a function that installs a fake DB returning the given rows.

    Uses FastAPI's app.dependency_overrides (the documented escape hatch)
    so we don't have to monkey-patch module globals. The fixture cleans
    up after every test to avoid leaking state into the smoke tests
    in test_health.py that intentionally exercise the real `get_db`.
    """
    installed = []

    def _install(rows: List[Campaign]):
        def _override():
            session = _FakeSession(rows)
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = _override
        installed.append(get_db)

    try:
        yield _install
    finally:
        for dep in installed:
            app.dependency_overrides.pop(dep, None)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_list_campaigns_returns_empty_list_when_no_rows(override_db):
    override_db([])

    response = client.get("/campaigns")

    assert response.status_code == 200
    assert response.json() == []


def test_list_campaigns_returns_serialized_rows(override_db):
    override_db([
        _make_campaign(id="cmp_001", campaign_code="CMP-001", name="Spring Launch"),
        _make_campaign(id="cmp_002", campaign_code="CMP-002", name="Summer Push"),
    ])

    response = client.get("/campaigns")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    ids = [row["id"] for row in body]
    assert ids == ["cmp_001", "cmp_002"]


def test_list_campaigns_response_has_documented_shape(override_db):
    override_db([_make_campaign()])

    response = client.get("/campaigns")

    assert response.status_code == 200
    row = response.json()[0]

    # Required fields per CampaignOut. If any of these disappear we want
    # to know — frontend code in frontend/src/api/client.js depends on them.
    for field in (
        "id",
        "campaign_code",
        "name",
        "advertiser",
        "status",
        "objective",
        "start_date",
        "end_date",
        "budget_usd",
        "created_at",
        "updated_at",
    ):
        assert field in row, f"missing required field: {field}"

    assert row["budget_usd"] == 100000.0
    # datetimes serialize to ISO strings via Pydantic
    assert row["start_date"].startswith("2026-01-01")


def test_list_campaigns_serializes_optional_fields_as_null(override_db):
    override_db([
        _make_campaign(channel=None, owner_name=None, region=None),
    ])

    response = client.get("/campaigns")

    assert response.status_code == 200
    row = response.json()[0]
    assert row["channel"] is None
    assert row["owner_name"] is None
    assert row["region"] is None


# ---------------------------------------------------------------------------
# Error contracts
# ---------------------------------------------------------------------------


def test_list_campaigns_translates_runtime_error_to_503(override_db):
    """If the DB dependency raises RuntimeError, main.py's exception handler
    must surface it as a 503 with a JSON `detail`. This is the contract that
    lets the app boot without DATABASE_URL — see backend/CLAUDE.md."""

    def _broken_get_db():
        raise RuntimeError("DATABASE_URL environment variable is not set.")
        yield  # pragma: no cover — make this a generator function

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        response = client.get("/campaigns")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "DATABASE_URL" in body["detail"]


def test_post_campaigns_returns_405():
    """/campaigns is read-only today. A POST should be rejected by FastAPI's
    routing layer with 405, not silently fall through to another handler."""
    response = client.post("/campaigns", json={"name": "x"})
    assert response.status_code == 405


def test_unknown_route_returns_404():
    response = client.get("/definitely-not-a-real-route-12345")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Trailing-slash behavior
# ---------------------------------------------------------------------------


def test_list_campaigns_trailing_slash_is_handled(override_db):
    """The router declares the empty path (`""`) under prefix `/campaigns`,
    which means `/campaigns` is the canonical URL. `/campaigns/` should
    either work directly or redirect — both are acceptable; what we don't
    want is a 404. This pins the behavior so we notice if it changes."""
    override_db([])

    response = client.get("/campaigns/", follow_redirects=True)

    assert response.status_code == 200
    assert response.json() == []
