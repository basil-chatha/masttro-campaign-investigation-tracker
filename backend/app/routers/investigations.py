"""
Investigations router — investigation CRUD endpoints.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Investigation, Campaign
from app.schemas import InvestigationCreate, InvestigationOut

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationOut)
def create_investigation(payload: InvestigationCreate, db: Session = Depends(get_db)):
    """Create a new investigation for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    now = datetime.utcnow()
    investigation = Investigation(
        id=f"inv_{uuid.uuid4().hex[:12]}",
        campaign_id=payload.campaign_id,
        source_snapshot_id=payload.source_snapshot_id,
        issue_type=payload.issue_type,
        severity=payload.severity,
        status="New",
        owner_name=payload.owner_name,
        question=payload.question,
        hypothesis=payload.hypothesis,
        next_action=payload.next_action,
        opened_at=now,
        updated_at=now,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    """Get a single investigation by ID."""
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.get("", response_model=List[InvestigationOut])
def list_investigations(campaign_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List all investigations, optionally filtered by campaign_id."""
    query = db.query(Investigation)
    if campaign_id:
        query = query.filter(Investigation.campaign_id == campaign_id)
    return query.order_by(Investigation.opened_at.desc()).all()
