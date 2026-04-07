# Campaign Investigation Tracker — Week 1 Pilot Plan

## Pilot scope

One team. One workflow. One repo. One measure.

This pilot validates a single workflow end to end before any broader rollout. The goal is evidence that the workflow is repeatable and measurable, not that it is feature-complete.

| Constraint | Decision |
|---|---|
| Team | Campaign Operations (or one named squad) |
| Workflow | Unhealthy campaign triage and investigation |
| Repo | This repo (`campaign-investigation-tracker`) |
| Approval chain | Workflow owner reviews all investigation resolutions |
| Success measure | Investigation cycle time (opened to resolved) |

## The pilot workflow

The end-to-end workflow the pilot team will run:

1. **Browse campaigns** — Open the campaign list. Campaigns with anomaly flags are visually marked.
2. **Open a flagged campaign** — Navigate to the campaign detail page. Review health snapshots (impressions, CTR, viewability, spend pacing, delivery rate) to understand the issue.
3. **Start an investigation** — Click "Start Investigation" on the campaign detail page. Fill in structured fields:
   - **Issue type** — e.g., Low CTR, Underdelivery, Pacing Issue
   - **Severity** — Critical, High, Medium, or Low
   - **Owner** — who is responsible for this investigation
   - **Question** — what are we trying to find out?
   - **Hypothesis** — what do we think is causing this?
   - **Next action** — what should we do first?
4. **Progress the investigation** — Move through statuses: New → Investigating → Needs Action → Resolved.
5. **Capture evidence** — Attach typed evidence items (Metric, Delivery Note, Operator Note, QA Check, Recommendation) as the investigation proceeds.
6. **Resolve** — Record a resolution summary and mark the investigation as Resolved.

## What is pilot-ready today

Modules 01–06 have delivered:

- Campaign list with health badge indicators
- Campaign detail page with health snapshot history
- Investigation creation form with structured fields (question, hypothesis, owner, next_action, severity, issue_type)
- Investigation list per campaign (newest first)
- AI economics scaffold (`AiRun` model and read endpoints) for future usage tracking
- Shared `CLAUDE.md` with architecture, conventions, approval boundaries, and investigation workflow rules
- Shared command: `/investigation-plan` for planning investigation-related code changes
- Project-scoped MCP configuration (`.mcp.json`)
- Backend test harness with connectivity tests

The pilot team can browse campaigns, identify unhealthy ones, and create structured investigations today.

## What is NOT yet production-ready

Be explicit about gaps so the pilot team knows what to work around:

| Gap | Impact on pilot | Planned for |
|---|---|---|
| No status update endpoint (PATCH) | Status changes require direct DB access or manual tracking | Day 2 — Module 03 |
| No evidence capture UI | Evidence must be logged outside the app during the pilot | Day 2 |
| No AI usage display | AI economics data exists but is not surfaced in the UI | Day 2 — Module 05 |
| No authentication or RBAC | All users share access; trust-based during pilot | Post-pilot if needed |
| No background jobs or notifications | Manual checking required; no alerts on status changes | Post-pilot |
| Tests are connectivity-only | No integration tests against real data; no frontend tests | Incremental during pilot |
| No investigation detail page | Investigations are listed but have no dedicated view | Day 2 |

These gaps are acceptable for a narrow pilot with a small team. They are not acceptable for broader rollout.

## KPI baselines

Measure these before and during the pilot. Capture the "before" state in Week 1.

| Metric | What it measures | Baseline source | Target direction |
|---|---|---|---|
| Investigation cycle time | Hours from opened_at to resolved_at | Manual tracking or DB query | Decrease |
| Time to first hypothesis | Minutes from anomaly detection to investigation creation | Observation during pilot | Decrease |
| Evidence items per investigation | Count of evidence records per resolved investigation | DB query | Increase (to a useful level, not infinite) |
| Review rounds per investigation | Handoffs or re-reviews before resolution | Workflow owner tracking | Decrease |
| AI cost per investigation | Sum of estimated_cost_usd from ai_runs per investigation | ai_runs table | Visible and bounded |
| Rework rate | Investigations reopened or re-triaged after resolution | Status history | Decrease |

## Ownership

Every standard needs an owner or it will drift.

| Responsibility | Owner (assign by name) |
|---|---|
| Pilot workflow and daily operations | ___________________ |
| `CLAUDE.md` and shared repo standards | ___________________ |
| MCP configuration and tool integrations | ___________________ |
| KPI measurement and weekly reporting | ___________________ |
| Day 2 productionization decisions | ___________________ |

## Non-goals

The pilot is intentionally narrow. These are explicitly out of scope:

- Full campaign operations platform (we are building one workflow, not an ops suite)
- Broad analytics or reporting dashboards
- Complex external integrations (ad servers, DSPs, third-party APIs)
- Authentication, authorization, or role-based access control
- Background processing, job queues, or automated notifications
- Multi-team or cross-functional rollout
- Performance optimization or horizontal scaling
- Mobile or responsive layout work

If someone asks "can we also add X?" during the pilot, the answer is: add it to the Day 2 backlog, not to the pilot.

## Pilot readiness checklist

Confirm before starting:

- [x] Shared `CLAUDE.md` exists and covers conventions, workflow rules, and approval boundaries
- [x] `.mcp.json` approach is agreed and committed
- [x] One shared command (`/investigation-plan`) is defined and usable
- [ ] Local secrets and auth requirements are documented for each pilot participant
- [ ] Workflow owner is named (see Ownership table above)
- [ ] Success metrics are written down and baseline "before" state is captured
- [ ] One skill candidate has been identified for Day 2 (e.g., investigation triage skill)
- [ ] Pilot participants have local dev environments running

## Bridge to Day 2

Day 2 turns this pilot into infrastructure.

| Day 2 topic | What it adds to the pilot |
|---|---|
| Skills (Module 01) | Reusable investigation triage workflow with consistent behavior |
| Hooks (Module 02) | Automated guardrails — enforce formatting, block dangerous commands |
| Parallel execution (Module 03) | Investigation status progression built via parallel streams |
| Custom agents (Module 04) | Specialist review agent scoped to investigation quality |
| Production rollout (Module 05) | AI usage display, final rollout artifact, ownership and cadence |

## 30/60/90 path

### Week 1
- Run the investigation workflow end to end with the pilot team
- Collect baseline timing and quality evidence
- Log breakdowns in instructions, tooling, or approvals

### 30 days
- Refine `CLAUDE.md` and shared commands based on pilot experience
- Identify one workflow ready to become a shared skill
- Confirm the workflow is repeatable, not just impressive once

### 60 days
- Deploy at least one shared skill
- Add one automation hook where justified by evidence
- Expand only after ownership and review are stable

### 90 days
- Compare results against KPI baselines
- Decide what to standardize, what to keep experimental, and what to stop
- Present a measured recommendation for wider rollout

## Decision gate

Do not expand beyond this pilot unless all of the following are true:

- Shared standards exist and are maintained
- The investigation workflow has worked repeatedly (not just once)
- Owners are named and active
- KPIs are being tracked and reported
- Approval gates are holding

Without these conditions, scaling amplifies confusion rather than value.
