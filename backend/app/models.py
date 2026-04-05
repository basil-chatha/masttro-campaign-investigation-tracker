"""
SQLAlchemy ORM models for the Campaign Investigation Tracker.

Only the campaign-related models are mapped here — the investigation
workflow models (investigations, investigation_evidence, ai_runs) will
be built during the workshop.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add SQLAlchemy relationship from Campaign
#   to CampaignHealth (e.g. `health_snapshots = relationship("CampaignHealth", back_populates=...)`)
#   so the campaign detail endpoint can eagerly load health data.

# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add SQLAlchemy relationship from Campaign
#   to Investigation (e.g. `investigations = relationship("Investigation", back_populates=...)`)
#   so the campaign detail page can show associated investigations.


class Campaign(Base):
    """Campaign table — represents a marketing campaign."""
    __tablename__ = "campaigns"

    id = Column(String(50), primary_key=True, index=True)
    campaign_code = Column(String(50), unique=True, index=True)
    name = Column(String(255))
    advertiser = Column(String(255))
    status = Column(String(50))
    objective = Column(String(255))
    channel = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    budget_usd = Column(Float)
    owner_name = Column(String(255))
    region = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignHealth(Base):
    """Campaign health snapshots — time-series performance data."""
    __tablename__ = "campaign_health"

    id = Column(String(50), primary_key=True, index=True)
    campaign_id = Column(String(50), ForeignKey("campaigns.id"), index=True)
    snapshot_at = Column(DateTime)
    impressions = Column(Integer)
    clicks = Column(Integer)
    ctr = Column(Float)
    viewability = Column(Float)
    completion_rate = Column(Float)
    spend_usd = Column(Float)
    budget_pacing_pct = Column(Float)
    delivery_rate_pct = Column(Float)
    anomaly_flag = Column(Boolean, default=False)
    anomaly_reason = Column(String(255))
    delivery_note = Column(Text)


# TODO [Step 2 — Day 1 / Module 02 — Economics]: Add the AiRun ORM model.
#   Maps to the `ai_runs` table. Columns: id, investigation_id (FK → investigations.id),
#   model, task_type, input_tokens, output_tokens, estimated_cost_usd, latency_ms,
#   prompt_summary, recommendation_summary, created_at.
#   This gives the product a concrete place to log AI activity for economics discussion.
#   Keep it intentionally minimal — enough to log model, latency, token/cost estimate,
#   and which investigation it relates to.


# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add the Investigation ORM model.
#   Maps to the `investigations` table. Columns: id, campaign_id (FK → campaigns.id),
#   source_snapshot_id (FK → campaign_health.id), issue_type, severity, status, owner_name,
#   question, hypothesis, next_action, resolution_summary, opened_at, updated_at, resolved_at.
#   Core fields to capture live: question, hypothesis, owner, next_action.
#   Status workflow: New → Investigating → Needs Action → Resolved.


# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add the InvestigationEvidence ORM model.
#   Maps to the `investigation_evidence` table. Columns: id, investigation_id (FK → investigations.id),
#   snapshot_id (FK → campaign_health.id), evidence_type, title, summary, metric_name,
#   metric_value, metric_unit, source_label, source_ref, captured_at, captured_by,
#   is_key_evidence, sort_order.
#   Typed evidence: metrics, notes, QA checks, recommendations.
