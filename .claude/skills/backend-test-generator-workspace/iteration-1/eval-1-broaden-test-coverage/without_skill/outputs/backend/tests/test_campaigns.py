"""
Tests for the /campaigns router with a real (in-memory) database.

The existing test_health.py covers only the "DB not configured" path
(accepts 200 OR 503). That means the actual SQL query, ORM->Pydantic
serialization, and CampaignOut field contract are *completely* untested.

These tests wire an in-memory SQLite DB into the FastAPI app via
dependency_overrides, seed a couple of Campaign rows, and exercise the
full request path: HTTP -> router -> SQLAlchemy query -> CampaignOut.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, Campaign, CampaignHealth


@pytest.fixture
def db_session():
    """Fresh in-memory SQLite DB with the ORM schema applied, per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient with get_db overridden to yield the in-memory session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            # The db_session fixture owns close()
            pass

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _make_campaign(**overrides):
    """Build a Campaign ORM row with sensible defaults."""
    base = dict(
        id="camp_001",
        campaign_code="C-001",
        name="Spring Launch",
        advertiser="Acme Co",
        status="active",
        objective="awareness",
        channel="display",
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 3, 31),
        budget_usd=10_000.0,
        owner_name="Alice",
        region="NA",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    base.update(overrides)
    return Campaign(**base)


def test_list_campaigns_returns_empty_list_when_no_rows(client):
    """Empty DB should return [], not 500 and not 404."""
    response = client.get("/campaigns")
    assert response.status_code == 200
    assert response.json() == []


def test_list_campaigns_returns_seeded_rows(client, db_session):
    """A seeded campaign should round-trip through CampaignOut."""
    db_session.add(_make_campaign())
    db_session.commit()

    response = client.get("/campaigns")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    row = body[0]
    assert row["id"] == "camp_001"
    assert row["campaign_code"] == "C-001"
    assert row["name"] == "Spring Launch"
    assert row["advertiser"] == "Acme Co"
    assert row["status"] == "active"
    assert row["objective"] == "awareness"
    assert row["channel"] == "display"
    assert row["budget_usd"] == 10_000.0
    assert row["owner_name"] == "Alice"
    assert row["region"] == "NA"
    # Datetime fields must be present and ISO-serializable (Pydantic does this).
    assert "start_date" in row and row["start_date"].startswith("2026-01-01")
    assert "end_date" in row and row["end_date"].startswith("2026-03-31")
    assert "created_at" in row
    assert "updated_at" in row


def test_list_campaigns_returns_multiple_rows(client, db_session):
    """All rows should be returned; no implicit limit/filter."""
    db_session.add_all([
        _make_campaign(id="camp_001", campaign_code="C-001", name="Alpha"),
        _make_campaign(id="camp_002", campaign_code="C-002", name="Beta"),
        _make_campaign(id="camp_003", campaign_code="C-003", name="Gamma"),
    ])
    db_session.commit()

    response = client.get("/campaigns")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    names = {row["name"] for row in body}
    assert names == {"Alpha", "Beta", "Gamma"}


def test_list_campaigns_handles_nullable_optional_fields(client, db_session):
    """CampaignOut declares channel/owner_name/region as Optional.

    Storing a row with those fields as NULL must serialize to JSON null,
    not 500. This catches regressions if someone tightens the schema.
    """
    db_session.add(_make_campaign(
        id="camp_nullable",
        campaign_code="C-NULL",
        channel=None,
        owner_name=None,
        region=None,
    ))
    db_session.commit()

    response = client.get("/campaigns")
    assert response.status_code == 200
    row = response.json()[0]
    assert row["channel"] is None
    assert row["owner_name"] is None
    assert row["region"] is None


def test_campaigns_endpoint_uses_get_db_dependency(client, db_session):
    """Smoke test that the dependency override is wired correctly.

    If campaigns.py stops using Depends(get_db), our override would be
    bypassed and this test would still pass — but the prior tests would
    fail with 503 because the real DATABASE_URL is unset. So this is
    really a sanity check that the fixture chain holds.
    """
    response = client.get("/campaigns")
    assert response.status_code == 200
