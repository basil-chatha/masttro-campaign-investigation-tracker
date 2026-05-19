"""
Tests for Pydantic schemas in app/schemas.py.

These are pure unit tests — no DB, no HTTP. They guard against:
- accidental removal of `from_attributes=True` (breaks ORM->schema flow)
- field type drift (e.g. budget_usd becoming Optional silently)
- required-vs-optional flips that would change the OpenAPI contract

Today CampaignOut is the only schema. New schemas added during the workshop
(CampaignDetailOut, InvestigationOut, etc.) should grow tests in this file.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas import CampaignOut


def _campaign_attrs(**overrides):
    """Object that mimics a Campaign ORM instance via attribute access."""
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
    return SimpleNamespace(**base)


def test_campaign_out_validates_from_orm_like_object():
    """from_attributes=True must allow building a schema from an ORM row."""
    out = CampaignOut.model_validate(_campaign_attrs())
    assert out.id == "camp_001"
    assert out.budget_usd == 10_000.0


def test_campaign_out_serializes_to_expected_json_shape():
    """model_dump() output should match what the API returns.

    Pin the field set so dropping a field is a loud failure.
    """
    out = CampaignOut.model_validate(_campaign_attrs())
    dumped = out.model_dump()
    assert set(dumped.keys()) == {
        "id", "campaign_code", "name", "advertiser", "status", "objective",
        "channel", "start_date", "end_date", "budget_usd", "owner_name",
        "region", "created_at", "updated_at",
    }


def test_campaign_out_allows_null_optional_fields():
    """channel, owner_name, region are Optional — None must validate."""
    out = CampaignOut.model_validate(_campaign_attrs(
        channel=None, owner_name=None, region=None
    ))
    assert out.channel is None
    assert out.owner_name is None
    assert out.region is None


def test_campaign_out_rejects_missing_required_field():
    """Required fields (e.g. id) must raise ValidationError when absent."""
    bad = _campaign_attrs()
    delattr(bad, "id")
    with pytest.raises(ValidationError):
        CampaignOut.model_validate(bad)


def test_campaign_out_rejects_wrong_type_for_budget():
    """budget_usd must coerce/reject non-numeric values.

    Pydantic v2 will coerce numeric strings, but a non-numeric string
    must raise ValidationError so the frontend never sees garbage.
    """
    with pytest.raises(ValidationError):
        CampaignOut.model_validate(_campaign_attrs(budget_usd="not-a-number"))


def test_campaign_out_required_fields_are_not_optional():
    """Pin which fields are required vs optional in the OpenAPI contract."""
    schema = CampaignOut.model_json_schema()
    required = set(schema.get("required", []))

    # These MUST stay required — frontend assumes them.
    assert {
        "id", "campaign_code", "name", "advertiser", "status", "objective",
        "start_date", "end_date", "budget_usd", "created_at", "updated_at",
    }.issubset(required)

    # These are explicitly Optional in the schema today.
    assert "channel" not in required
    assert "owner_name" not in required
    assert "region" not in required
