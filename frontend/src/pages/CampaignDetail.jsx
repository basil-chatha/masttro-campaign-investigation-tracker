import { useParams, Link } from 'react-router-dom';

// TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Import { useState, useEffect } from 'react'
//   and import getCampaign (or getCampaignHealth) from '../api/client' once those
//   API functions are built. Load campaign data + health snapshots on mount.

// TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Import createInvestigation and
//   getInvestigations from '../api/client' once those API functions are built.

// TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Import updateInvestigationStatus
//   from '../api/client' for the status progression UI.

// TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Import getAiRuns from '../api/client'
//   for the AI usage card on the investigation detail view.

export default function CampaignDetail() {
  const { id } = useParams();

  // TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add state for campaign data, health snapshots,
  //   loading, and error. Fetch campaign detail (with health data) on component mount using
  //   useEffect. This is the AIDLC demo vehicle — plan the approach in plan mode first,
  //   clarify required fields and what success means, then implement.

  // TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add state for investigations list.
  //   Fetch investigations for this campaign on mount. Display them below the campaign info.

  return (
    <div>
      <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
        &larr; Back to campaigns
      </Link>

      <h2 className="mt-4 text-2xl font-semibold">Campaign Detail</h2>

      {/* TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Replace this placeholder with real campaign
          detail display. Show campaign metadata (name, advertiser, status, budget, dates, etc.)
          and a summary of health snapshots (e.g. latest CTR, viewability, anomaly flags).
          Include a small evidence summary section. */}
      <div className="mt-4 rounded-lg border p-6">
        <p className="text-sm text-muted-foreground">Campaign ID: {id}</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Detail view and investigation workflow will be built during the workshop.
        </p>
      </div>

      {/* TODO [Step 4 — Day 1 / Module 04 — AIDLC]: Add a "Start Investigation" button
          as a visible entry point. This is the bridge into the full investigation workflow
          built in Step 5. The button should open a form or modal for creating a new investigation. */}

      {/* TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add the investigation creation form.
          Capture core fields: question, hypothesis, owner_name, next_action, issue_type, severity.
          On submit, call createInvestigation() and refresh the investigations list.
          This is the "ticket-sized workflow" — form capture and persistence. */}

      {/* TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add an investigations list section.
          Display existing investigations for this campaign with their status, question,
          owner, and severity. Each investigation should be clickable for detail view. */}

      {/* TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add investigation status
          progression UI. Each investigation card/row should show its current status with
          a visual indicator and allow status transitions:
          New → Investigating → Needs Action → Resolved.
          Include a status dropdown or button group that calls updateInvestigationStatus().
          This is the bounded parallel-work feature — one stream for backend logic,
          one for this frontend UI, one for tests. */}

      {/* TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Add an AI usage card or
          recommendation note section on the investigation detail view. Surface data from
          ai_runs: model used, token count, estimated cost, latency, and recommendation summary.
          This closes the economics loop from Step 2 — making AI usage visible in the product. */}
    </div>
  );
}
