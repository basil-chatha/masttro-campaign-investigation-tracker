# Campaign Investigation Tracker

## Architecture

- **Backend**: FastAPI (Python) with SQLAlchemy ORM, served by Uvicorn
- **Frontend**: React 18 + React Router v6 + Tailwind CSS + shadcn/ui, bundled by Vite
- **Database**: PostgreSQL via Supabase (local dev with Supabase CLI)
- **Layout**: `backend/` (FastAPI app), `frontend/` (React SPA), `supabase/` (migrations + seed data)

## Coding conventions

- Prefer extending existing patterns over introducing new abstractions.
- Backend endpoints live in `backend/app/routers/` as FastAPI `APIRouter` modules.
- ORM models go in `backend/app/models.py`; Pydantic response/request schemas in `backend/app/schemas.py`.
- Database access uses dependency injection: `db: Session = Depends(get_db)`.
- Frontend pages live in `frontend/src/pages/`; shared UI components in `frontend/src/components/`.
- API calls from the frontend go through `frontend/src/api/client.js`.

## Entity ID and creation patterns

- New entity IDs follow the pattern `prefix_` + 12 hex chars from uuid4: e.g., `inv_`, `ev_`.
- Timestamps default to `datetime.utcnow()` at creation; `updated_at` uses `onupdate=datetime.utcnow`.
- New routers must be registered in `backend/app/main.py` via `app.include_router(router)`.

## Testing

- Run backend tests: `cd backend && uv run pytest`
- Tests live in `backend/tests/` and use `TestClient(app)` directly (no DB fixtures).
- Connectivity tests accept status codes `[200, 404, 503]` — 503 means DATABASE_URL is unset, which is valid in CI.
- New endpoints need at least a basic connectivity test.

## Frontend patterns

- Data fetching uses `useEffect` with a stale-check cleanup flag and `loading`/`error`/`data` state triple.
- Parallel fetches use `Promise.all` (see `CampaignDetail.jsx`).

## Shared commands

- `/investigation-plan <description>` — plans an investigation-related change by reading domain files, identifying affected code, proposing an approach, and flagging risks.

## Approval boundaries

- Any schema or migration change requires explicit human approval.
- Do not modify `supabase/migrations/` or `supabase/seed.sql` without review.
- Do not commit secrets, `.env` files, or API tokens.

## Investigation workflow

- Status progression: New -> Investigating -> Needs Action -> Resolved.
- Evidence types: Metric, Delivery Note, Operator Note, QA Check, Recommendation.
- Core investigation fields: question, hypothesis, owner, next_action.

## Pilot plan

- The Week 1 pilot plan lives in `docs/pilot-plan.md`.
- It defines the narrow workflow scope, KPI baselines, ownership, non-goals, and the 30/60/90 path from pilot to production.
- Do not expand the pilot scope without updating this artifact and confirming the decision gate criteria are met.

## What stays local (not in this repo)

- `.env` files with database URLs, API keys, and secrets
- Personal Claude Code preferences (`~/.claude/`)
- MCP authentication tokens (handled per-user via OAuth)
