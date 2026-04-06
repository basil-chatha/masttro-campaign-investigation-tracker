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

## Testing

- Run backend tests: `cd backend && pytest`
- Tests live in `backend/tests/`.
- New endpoints should have at least a basic connectivity test.

## Approval boundaries

- Any schema or migration change requires explicit human approval.
- Do not modify `supabase/migrations/` or `supabase/seed.sql` without review.
- Do not commit secrets, `.env` files, or API tokens.

## Investigation workflow

- Status progression: New -> Investigating -> Needs Action -> Resolved.
- Evidence types: Metric, Delivery Note, Operator Note, QA Check, Recommendation.
- Core investigation fields: question, hypothesis, owner, next_action.

## What stays local (not in this repo)

- `.env` files with database URLs, API keys, and secrets
- Personal Claude Code preferences (`~/.claude/`)
- MCP authentication tokens (handled per-user via OAuth)
