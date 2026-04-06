"""
Pydantic response schemas for API responses.

Only the campaign list schema is defined here — additional schemas
for health snapshots, investigations, and AI runs will be built
during the workshop as new endpoints are added.
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict


class CampaignOut(BaseModel):
    """Response schema for a campaign."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_code: str
    name: str
    advertiser: str
    status: str
    objective: str
    channel: Optional[str] = None
    start_date: datetime
    end_date: datetime
    budget_usd: float
    owner_name: Optional[str] = None
    region: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    needs_help: bool = False


class CampaignHealthOut(BaseModel):
    """Response schema for a campaign health snapshot."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    snapshot_at: datetime
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: float
    viewability: float
    completion_rate: Optional[float] = None
    spend_usd: float
    budget_pacing_pct: Optional[float] = None
    delivery_rate_pct: Optional[float] = None
    anomaly_flag: Optional[bool] = False
    anomaly_reason: Optional[str] = None
    delivery_note: Optional[str] = None


class CampaignDetailOut(CampaignOut):
    """Response schema for campaign detail with health snapshots."""
    health_snapshots: List[CampaignHealthOut] = []


Severity = Literal["Critical", "High", "Medium", "Low"]


class InvestigationCreate(BaseModel):
    """Request schema for creating a new investigation."""
    campaign_id: str
    source_snapshot_id: Optional[str] = None
    issue_type: str
    severity: Severity
    owner_name: Optional[str] = None
    question: str
    hypothesis: str
    next_action: str


class InvestigationOut(BaseModel):
    """Response schema for an investigation record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    source_snapshot_id: Optional[str] = None
    issue_type: str
    severity: str
    status: str
    owner_name: Optional[str] = None
    question: str
    hypothesis: str
    next_action: str
    resolution_summary: Optional[str] = None
    opened_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class InvestigationEvidenceOut(BaseModel):
    """Response schema for an investigation evidence record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    snapshot_id: Optional[str] = None
    evidence_type: str
    title: str
    summary: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    metric_unit: Optional[str] = None
    source_label: Optional[str] = None
    source_ref: Optional[str] = None
    captured_at: datetime
    captured_by: Optional[str] = None
    is_key_evidence: Optional[bool] = False
    sort_order: Optional[int] = None


# TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add InvestigationStatusUpdate Pydantic schema.
#   Fields: status (constrained to "New" | "Investigating" | "Needs Action" | "Resolved"),
#   resolution_summary (optional, required when status is "Resolved").
#   Used by the PATCH /investigations/{id}/status endpoint for status progression.


class AiRunOut(BaseModel):
    """Response schema for an AI run record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    model: str
    task_type: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None
    prompt_summary: Optional[str] = None
    recommendation_summary: Optional[str] = None
    created_at: datetime


# TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Add AiRunCreate Pydantic schema (if needed).
#   Fields for logging a new AI run. May be needed when surfacing the AI usage card
#   on the investigation detail page and closing the economics loop.
