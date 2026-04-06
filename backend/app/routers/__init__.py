# TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Create a new file
#   `investigations.py` in this directory. It should define an APIRouter with
#   prefix="/investigations" and implement:
#     - POST /investigations — create a new investigation (InvestigationCreate → InvestigationOut)
#     - GET /investigations/{id} — get a single investigation by id
#     - GET /investigations — list all investigations (optional: filter by campaign_id query param)
#   Core fields to capture: question, hypothesis, owner, next_action.

# TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add a status update endpoint
#   in `investigations.py`:
#     - PATCH /investigations/{id}/status — update investigation status
#   Status progression: New → Investigating → Needs Action → Resolved.
#   Use InvestigationStatusUpdate schema. Set resolved_at when status becomes "Resolved".

