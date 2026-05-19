"""
Campaigns router — campaign list endpoint.

Additional endpoints (campaign detail, health snapshots, investigations)
will be added during the workshop.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Campaign
from app.schemas import CampaignOut

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=List[CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db),
    name: Optional[str] = Query(
        None,
        description="Optional case-insensitive substring filter on campaign name.",
    ),
):
    """
    Get all campaigns.
    Returns a list of all campaigns in the system, optionally filtered by a
    case-insensitive substring match on campaign name.
    """
    query = db.query(Campaign)
    if name is not None and name.strip():
        query = query.filter(Campaign.name.ilike(f"%{name.strip()}%"))
    return query.all()


# TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add GET /campaigns/{campaign_id} endpoint.
#   Returns a single campaign with its associated health snapshots.
#   Use CampaignDetailOut as response_model. Query Campaign by id, join/load
#   CampaignHealth records. Raise 404 if campaign not found.
#   This is the AIDLC demo vehicle — plan the approach, clarify required fields
#   and what success means, then implement.


# TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add GET /campaigns/{campaign_id}/health endpoint.
#   Returns health snapshots for a specific campaign, ordered by snapshot_at.
#   Useful as a standalone endpoint for the frontend to fetch health data separately.


# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add GET /campaigns/{campaign_id}/investigations endpoint.
#   Returns all investigations for a given campaign.
#   Enables the campaign detail page to list existing investigations.
