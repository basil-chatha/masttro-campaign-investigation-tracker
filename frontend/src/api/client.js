/**
 * API client for the Campaign Investigation Tracker.
 *
 * Additional fetch functions (campaign detail, health snapshots,
 * investigations) will be added during the workshop as new
 * backend endpoints are built.
 */

const API_BASE = '/api';

// TODO [Step 2 — Day 1 / Module 02 — Economics]: When building out additional API functions below,
//   demonstrate model switching during development. Use a stronger model (e.g. Opus) for
//   planning the API client architecture and a cheaper/faster model (e.g. Haiku) for
//   routine implementation like writing repetitive fetch wrappers.
//   "Model choice is a workflow design decision — do not spend premium reasoning on repetitive tasks."

/**
 * Generic fetch wrapper with error handling.
 * @param {string} path — API path (prefixed with /api by the Vite proxy)
 */
async function fetchApi(path) {
  const url = `${API_BASE}${path}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch all campaigns.
 */
export async function getCampaigns() {
  return fetchApi('/campaigns');
}

/**
 * Fetch a single campaign with health snapshots.
 * @param {string} id — Campaign ID
 */
export async function getCampaign(id) {
  return fetchApi(`/campaigns/${id}`);
}

/**
 * Fetch health snapshots for a campaign.
 * @param {string} campaignId — Campaign ID
 */
export async function getCampaignHealth(campaignId) {
  return fetchApi(`/campaigns/${campaignId}/health`);
}

// TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add createInvestigation(data) function.
//   POSTs to /investigations with the investigation form data.
//   Needs to extend fetchApi or add a new fetchApiPost helper that supports
//   POST method with JSON body (the current fetchApi only supports GET).

// TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add getInvestigations(campaignId) function.
//   Fetches investigations for a campaign from GET /campaigns/{id}/investigations
//   or GET /investigations?campaign_id={id}.

// TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add updateInvestigationStatus(id, status, resolutionSummary) function.
//   PATCHes /investigations/{id}/status to progress investigation status.
//   Status flow: New → Investigating → Needs Action → Resolved.

// TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Add getAiRuns(investigationId) function.
//   Fetches AI run records from GET /investigations/{id}/ai-runs.
//   Surfaces AI usage data on the investigation detail view.
