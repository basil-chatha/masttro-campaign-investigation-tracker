"""
Campaigns router — campaign list endpoint.

Additional endpoints (campaign detail, health snapshots, investigations)
will be added during the workshop.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Campaign, CampaignHealth
from app.schemas import CampaignOut, CampaignDetailOut, CampaignHealthOut

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=List[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    """
    Get all campaigns.
    Returns a list of all campaigns in the system.
    """
    latest_sq = (
        db.query(
            CampaignHealth.campaign_id,
            func.max(CampaignHealth.snapshot_at).label("max_snapshot_at"),
        )
        .group_by(CampaignHealth.campaign_id)
        .subquery()
    )

    rows = (
        db.query(Campaign, CampaignHealth.anomaly_flag)
        .outerjoin(
            latest_sq,
            Campaign.id == latest_sq.c.campaign_id,
        )
        .outerjoin(
            CampaignHealth,
            and_(
                CampaignHealth.campaign_id == latest_sq.c.campaign_id,
                CampaignHealth.snapshot_at == latest_sq.c.max_snapshot_at,
            ),
        )
        .all()
    )

    results = []
    for campaign, anomaly_flag in rows:
        campaign.needs_help = bool(anomaly_flag)
        results.append(campaign)
    return results


@router.get("/{campaign_id}", response_model=CampaignDetailOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get a single campaign with its health snapshots."""
    campaign = (
        db.query(Campaign)
        .options(joinedload(Campaign.health_snapshots))
        .filter(Campaign.id == campaign_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    # Match list endpoint logic: check only the latest snapshot
    campaign.needs_help = bool(campaign.health_snapshots and campaign.health_snapshots[-1].anomaly_flag)
    return campaign


@router.get("/{campaign_id}/health", response_model=List[CampaignHealthOut])
def get_campaign_health(campaign_id: str, db: Session = Depends(get_db)):
    """Get health snapshots for a specific campaign, ordered by time."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return (
        db.query(CampaignHealth)
        .filter(CampaignHealth.campaign_id == campaign_id)
        .order_by(CampaignHealth.snapshot_at)
        .all()
    )


# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add GET /campaigns/{campaign_id}/investigations endpoint.
#   Returns all investigations for a given campaign.
#   Enables the campaign detail page to list existing investigations.
