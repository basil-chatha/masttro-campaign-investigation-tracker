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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add SQLAlchemy relationship from Campaign
#   to CampaignHealth (e.g. `health_snapshots = relationship("CampaignHealth", back_populates=...)`)
#   so the campaign detail endpoint can eagerly load health data.

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

    health_snapshots = relationship("CampaignHealth", back_populates="campaign", order_by="CampaignHealth.snapshot_at")
    investigations = relationship("Investigation", back_populates="campaign", order_by="Investigation.opened_at.desc()")


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

    campaign = relationship("Campaign", back_populates="health_snapshots")


class AiRun(Base):
    """AI run log — tracks model usage, cost, and latency per investigation."""
    __tablename__ = "ai_runs"

    id = Column(String(50), primary_key=True, index=True)
    investigation_id = Column(String(50), ForeignKey("investigations.id"), index=True)
    model = Column(String(100))
    task_type = Column(String(100))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    estimated_cost_usd = Column(Float)
    latency_ms = Column(Integer)
    prompt_summary = Column(Text)
    recommendation_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Investigation(Base):
    """Investigation record — tracks a campaign performance issue through resolution."""
    __tablename__ = "investigations"

    id = Column(String(50), primary_key=True, index=True)
    campaign_id = Column(String(50), ForeignKey("campaigns.id"), index=True)
    source_snapshot_id = Column(String(50), ForeignKey("campaign_health.id"), nullable=True)
    issue_type = Column(String(100))
    severity = Column(String(50))
    status = Column(String(50))
    owner_name = Column(String(255), nullable=True)
    question = Column(Text)
    hypothesis = Column(Text)
    next_action = Column(Text)
    resolution_summary = Column(Text, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    campaign = relationship("Campaign", back_populates="investigations")
    evidence = relationship("InvestigationEvidence", back_populates="investigation")


class InvestigationEvidence(Base):
    """Evidence record — typed evidence attached to an investigation."""
    __tablename__ = "investigation_evidence"

    id = Column(String(50), primary_key=True, index=True)
    investigation_id = Column(String(50), ForeignKey("investigations.id"), index=True)
    snapshot_id = Column(String(50), ForeignKey("campaign_health.id"), nullable=True)
    evidence_type = Column(String(100))
    title = Column(String(255))
    summary = Column(Text)
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(Float, nullable=True)
    metric_unit = Column(String(50), nullable=True)
    source_label = Column(String(255), nullable=True)
    source_ref = Column(String(255), nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow)
    captured_by = Column(String(255), nullable=True)
    is_key_evidence = Column(Boolean, default=False)
    sort_order = Column(Integer, nullable=True)

    investigation = relationship("Investigation", back_populates="evidence")
