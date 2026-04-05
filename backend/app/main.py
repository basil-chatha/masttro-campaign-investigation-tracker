"""
Campaign Investigation Tracker API
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import campaigns

# Initialize FastAPI app
app = FastAPI(
    title="Campaign Investigation Tracker API",
    description="Backend for investigating campaign performance issues and anomalies",
    version="0.1.0",
)

# CORS middleware - allow all origins for workshop simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Return a clear JSON error when the database isn't configured yet."""
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


# Register routers
app.include_router(campaigns.router)

# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Import and register the investigations router.
#   Create `app/routers/investigations.py` with an APIRouter(prefix="/investigations").
#   Then: `from app.routers import investigations` and `app.include_router(investigations.router)`.
#   This router handles investigation CRUD: create, list, get by id, and status updates.

# TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Import and register the ai_runs router.
#   Create `app/routers/ai_runs.py` with an APIRouter(prefix="/ai-runs").
#   Endpoints: GET /investigations/{id}/ai-runs (list AI runs for an investigation).
#   Surfaces AI usage data to close the economics loop from Step 2.


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Returns service status - useful for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "service": "campaign-investigation-tracker",
    }


@app.get("/")
def root():
    """
    Root endpoint - returns API info.
    """
    return {
        "message": "Campaign Investigation Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# =============================================================================
# NEW FILES TO CREATE DURING THE WORKSHOP
# =============================================================================

# TODO [Step 7 — Day 1 / Module 07 — Wrap-Up & Pilot Plan]: Create `docs/pilot-plan.md`
#   (or `pilot-plan.md` at the repo root). Define the narrow pilot around this exact
#   workflow: unhealthy campaign → investigation creation → evidence capture → next action.
#   Include: KPI baselines, named ownership, non-goals, and what makes the workflow
#   pilot-ready but not yet production-ready. Use the current state of the tracker
#   as the concrete example of a narrow Week 1 pilot.

# TODO [Step 8 — Day 2 / Module 01 — Team Skills]: Create `.claude/skills/investigation-triage/SKILL.md`.
#   Turn the repeated investigation workflow into a shared skill. Write a strong description:
#   triage a campaign issue, review investigation quality, check evidence completeness,
#   suggest next action. Keep it small and bounded. Run it against a real investigation
#   example so the room sees the difference between a skill and generic prompting.

# TODO [Step 9 — Day 2 / Module 02 — Automation Hooks]: Create `.claude/settings.json`.
#   Add one project-scoped hook — prefer a small, obviously valuable guardrail:
#     - A formatter/test hook that runs after edits (e.g. run pytest after Python changes)
#     - Or a Bash safety guard that blocks dangerous commands (explain exit 2 as block signal)
#   Keep it directly relevant to the repo. Restart or narrate restart behavior after change.
#   Example: { "hooks": { "PostToolUse": [{ "matcher": "Edit", "command": "..." }] } }

# TODO [Step 11 — Day 2 / Module 04 — Advanced Role Tracks]: Create `.claude/agents/investigation-reviewer.md`.
#   Define a narrow custom agent scoped to review changes touching investigations,
#   evidence capture, status transitions, or AI usage notes. Keep it review-oriented
#   rather than autonomous. This shows how specialist judgment becomes a reusable repo asset.

# TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Create `docs/production-rollout.md`
#   (or `production-rollout.md` at the repo root). Write the minimum viable setup:
#   shared CLAUDE.md, one shared skill, one hook, one approved parallel workflow,
#   named owners, KPI cadence. Show which parts of the tracker are pilot-ready
#   versus what still should not be standardized or automated.
