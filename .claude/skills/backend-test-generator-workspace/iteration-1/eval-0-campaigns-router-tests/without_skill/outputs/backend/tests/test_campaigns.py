"""
Tests for the campaigns router (`app/routers/campaigns.py`).

Two layers of coverage:

1. Route-existence / contract tests against the real `app` — these mirror
   the convention in `tests/test_health.py` and tolerate a 503 when
   DATABASE_URL is not configured (see the lazy-DB pattern documented in
   `backend/CLAUDE.md`). They guarantee the route is registered, the
   prefix is `/campaigns`, and the response shape is sensible.

2. Functional tests that override the `get_db` dependency with an
   in-memory SQLite session populated with fixture campaigns. These
   exercise the router code path end-to-end (query, ORM → Pydantic
   serialization via `CampaignOut`) without requiring Postgres or the
   workshop seed data.

Only the currently-implemented endpoint (GET /campaigns) is covered.
The router has TODOs for `GET /campaigns/{id}` and
`GET /campaigns/{id}/health` that are not yet implemented; assertions
for those routes deliberately verify that they currently return 404 so
the suite will fail loudly when the workshop step lands without
matching test updates.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, Campaign


# ---------------------------------------------------------------------------
# Layer 1: contract tests against the real app (no DB override).
# ---------------------------------------------------------------------------

client = TestClient(app)


def test_list_campaigns_route_is_registered():
    """GET /campaigns must be routable.

    Accept 200 (DB available) or 503 (DB not configured) — the latter is
    raised by the lazy DB initializer in `app/database.py` and converted
    to 503 by the RuntimeError handler in `app/main.py`. Anything else
    (404, 500) means the route is broken.
    """
    response = client.get("/campaigns")
    assert response.status_code in (200, 503), (
        f"Unexpected status {response.status_code}: {response.text}"
    )


def test_list_campaigns_returns_json_list_when_db_available():
    """If the DB is available, the response body should be a JSON list."""
    response = client.get("/campaigns")
    if response.status_code == 503:
        pytest.skip("DATABASE_URL not configured; skipping live-DB shape check.")

    body = response.json()
    assert isinstance(body, list), f"Expected a JSON list, got: {type(body).__name__}"


def test_list_campaigns_503_payload_shape():
    """When the DB isn't configured, the 503 must come from the RuntimeError handler."""
    response = client.get("/campaigns")
    if response.status_code != 503:
        pytest.skip("Database is configured; cannot exercise the 503 branch.")

    body = response.json()
    assert "detail" in body
    # The RuntimeError text comes from `_init_db` and mentions DATABASE_URL.
    assert "DATABASE_URL" in body["detail"]


def test_campaigns_router_has_correct_prefix_and_tag():
    """The router should be mounted under /campaigns with tag 'campaigns'."""
    paths = [
        route.path for route in app.routes if getattr(route, "path", "").startswith("/campaigns")
    ]
    assert "/campaigns" in paths, f"/campaigns not found in registered routes: {paths}"

    # Also confirm the OpenAPI schema tags the operation correctly.
    schema = app.openapi()
    operation = schema["paths"]["/campaigns"]["get"]
    assert "campaigns" in operation.get("tags", [])


def test_unimplemented_campaign_detail_route_returns_404():
    """The campaign-detail endpoint is a workshop TODO; until implemented, it must 404.

    This guards against silent regressions: if a future edit accidentally
    registers the route without tests, this assertion will start
    failing and force a deliberate update.
    """
    response = client.get("/campaigns/some-campaign-id")
    assert response.status_code == 404


def test_unimplemented_campaign_health_route_returns_404():
    """Same guard for GET /campaigns/{id}/health (also a TODO)."""
    response = client.get("/campaigns/some-campaign-id/health")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Layer 2: functional tests with an overridden in-memory SQLite DB.
# ---------------------------------------------------------------------------

@pytest.fixture()
def sqlite_db():
    """Create a fresh in-memory SQLite engine and session factory per test.

    The Campaign model uses simple column types (String, Float, DateTime,
    Integer, Boolean, Text), all of which are supported by SQLite, so we
    can exercise the real router without Postgres.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client_with_db(sqlite_db):
    """TestClient with `get_db` overridden to yield an in-memory SQLite session."""
    TestingSessionLocal = sqlite_db

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    try:
        yield test_client, TestingSessionLocal
    finally:
        app.dependency_overrides.pop(get_db, None)


def _make_campaign(**overrides) -> Campaign:
    """Build a Campaign ORM instance with sensible defaults for tests."""
    now = datetime(2026, 1, 1, 12, 0, 0)
    defaults = dict(
        id="cmp-001",
        campaign_code="CMP-001",
        name="Spring Launch",
        advertiser="Acme Co",
        status="active",
        objective="awareness",
        channel="display",
        start_date=now,
        end_date=now + timedelta(days=30),
        budget_usd=10_000.0,
        owner_name="Alice Owner",
        region="NA",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Campaign(**defaults)


def test_list_campaigns_returns_empty_list_when_no_rows(client_with_db):
    """With an empty `campaigns` table, the endpoint returns an empty list (not 404)."""
    test_client, _ = client_with_db
    response = test_client.get("/campaigns")
    assert response.status_code == 200
    assert response.json() == []


def test_list_campaigns_returns_seeded_rows(client_with_db):
    """Seed two campaigns and assert both come back with the expected fields."""
    test_client, SessionLocal = client_with_db

    db = SessionLocal()
    try:
        db.add(_make_campaign(id="cmp-001", campaign_code="CMP-001", name="Spring Launch"))
        db.add(
            _make_campaign(
                id="cmp-002",
                campaign_code="CMP-002",
                name="Summer Promo",
                advertiser="Globex",
                status="paused",
                objective="conversion",
                channel="video",
                budget_usd=25_000.5,
                owner_name="Bob Owner",
                region="EMEA",
            )
        )
        db.commit()
    finally:
        db.close()

    response = test_client.get("/campaigns")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2

    by_id = {item["id"]: item for item in body}
    assert set(by_id) == {"cmp-001", "cmp-002"}

    first = by_id["cmp-001"]
    # Required fields per CampaignOut schema.
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
        assert field in first, f"Missing required field {field!r} in {first}"

    assert first["campaign_code"] == "CMP-001"
    assert first["name"] == "Spring Launch"
    assert first["advertiser"] == "Acme Co"
    assert first["status"] == "active"
    assert first["budget_usd"] == 10_000.0
    assert first["channel"] == "display"
    assert first["region"] == "NA"
    assert first["owner_name"] == "Alice Owner"

    second = by_id["cmp-002"]
    assert second["status"] == "paused"
    assert second["objective"] == "conversion"
    assert second["channel"] == "video"
    assert second["budget_usd"] == 25_000.5


def test_list_campaigns_serializes_optional_nullable_fields(client_with_db):
    """`channel`, `owner_name`, and `region` are Optional; nulls should pass through as None."""
    test_client, SessionLocal = client_with_db

    db = SessionLocal()
    try:
        db.add(
            _make_campaign(
                id="cmp-nullable",
                campaign_code="CMP-NULL",
                channel=None,
                owner_name=None,
                region=None,
            )
        )
        db.commit()
    finally:
        db.close()

    response = test_client.get("/campaigns")
    assert response.status_code == 200
    [row] = response.json()
    assert row["id"] == "cmp-nullable"
    assert row["channel"] is None
    assert row["owner_name"] is None
    assert row["region"] is None


def test_list_campaigns_serializes_datetimes_as_iso_strings(client_with_db):
    """Pydantic should serialize datetime columns to ISO-8601 strings the frontend can parse."""
    test_client, SessionLocal = client_with_db

    start = datetime(2026, 3, 1, 9, 30, 0)
    end = datetime(2026, 3, 31, 17, 0, 0)
    created = datetime(2026, 2, 15, 8, 0, 0)

    db = SessionLocal()
    try:
        db.add(
            _make_campaign(
                id="cmp-dates",
                campaign_code="CMP-DATES",
                start_date=start,
                end_date=end,
                created_at=created,
                updated_at=created,
            )
        )
        db.commit()
    finally:
        db.close()

    response = test_client.get("/campaigns")
    assert response.status_code == 200
    [row] = response.json()
    # We don't pin a specific format, but datetime fields must be strings
    # parseable back into datetime objects (ISO-8601 with optional offset).
    for field in ("start_date", "end_date", "created_at", "updated_at"):
        assert isinstance(row[field], str), f"{field} should serialize to a string"
        # `fromisoformat` accepts the standard FastAPI/Pydantic output.
        datetime.fromisoformat(row[field])


def test_list_campaigns_does_not_accept_post(client_with_db):
    """The router only registers GET; POST should be 405 Method Not Allowed."""
    test_client, _ = client_with_db
    response = test_client.post("/campaigns", json={})
    assert response.status_code == 405


def test_list_campaigns_trailing_slash_behavior(client_with_db):
    """Document the trailing-slash behavior of the route.

    The router is registered at "" under the /campaigns prefix, so the
    canonical path is `/campaigns` (no trailing slash). FastAPI will
    307-redirect `/campaigns/` to `/campaigns` by default. Either way,
    the request should not 404.
    """
    test_client, _ = client_with_db
    # follow_redirects defaults to True in TestClient's underlying httpx client.
    response = test_client.get("/campaigns/")
    assert response.status_code in (200, 307), (
        f"Expected 200 or 307 for trailing-slash variant, got {response.status_code}"
    )
