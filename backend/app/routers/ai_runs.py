"""
AI runs router — surfaces AI usage data for economics discussion.

Provides read-only endpoints to list AI run records (model, tokens,
cost, latency) tied to investigations.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AiRun
from app.schemas import AiRunOut

router = APIRouter(prefix="/ai-runs", tags=["ai-runs"])


@router.get("", response_model=List[AiRunOut])
def list_ai_runs(db: Session = Depends(get_db)):
    """List all AI run records."""
    return db.query(AiRun).order_by(AiRun.created_at.desc()).all()


@router.get("/investigation/{investigation_id}", response_model=List[AiRunOut])
def list_ai_runs_for_investigation(
    investigation_id: str, db: Session = Depends(get_db)
):
    """List AI run records for a specific investigation."""
    return (
        db.query(AiRun)
        .filter(AiRun.investigation_id == investigation_id)
        .order_by(AiRun.created_at.desc())
        .all()
    )
