import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCampaign } from '../api/client';
import { Badge } from '@/components/ui/badge';

// TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Import createInvestigation and
//   getInvestigations from '../api/client' once those API functions are built.

// TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Import updateInvestigationStatus
//   from '../api/client' for the status progression UI.

// TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Import getAiRuns from '../api/client'
//   for the AI usage card on the investigation detail view.

export default function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    getCampaign(id)
      .then((data) => { if (!stale) { setCampaign(data); setError(null); } })
      .catch((err) => { if (!stale) { setError(err.message); setCampaign(null); } })
      .finally(() => { if (!stale) setLoading(false); });
    return () => { stale = true; };
  }, [id]);

  // TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add state for investigations list.
  //   Fetch investigations for this campaign on mount. Display them below the campaign info.

  if (loading) return <p className="text-muted-foreground">Loading campaign...</p>;
  if (error) return <p className="text-destructive">Error: {error}</p>;
  if (!campaign) return <p className="text-muted-foreground">Campaign not found.</p>;

  const snapshots = campaign.health_snapshots || [];

  return (
    <div>
      <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
        &larr; Back to campaigns
      </Link>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-semibold">{campaign.name}</h2>
          <StatusBadge status={campaign.status} />
          {campaign.needs_help && <Badge variant="destructive">Needs Help</Badge>}
        </div>
        {/* TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Replace alert with
            real investigation creation form/modal. */}
        <button
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          onClick={() => alert('Investigation form coming in Module 05')}
        >
          Start Investigation
        </button>
      </div>

      <div className="mt-6 rounded-lg border p-6">
        <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm md:grid-cols-4">
          <Field label="Code" value={campaign.campaign_code} />
          <Field label="Advertiser" value={campaign.advertiser} />
          <Field label="Objective" value={campaign.objective} />
          <Field label="Channel" value={campaign.channel} />
          <Field label="Start" value={fmtDate(campaign.start_date)} />
          <Field label="End" value={fmtDate(campaign.end_date)} />
          <Field label="Budget" value={`$${campaign.budget_usd?.toLocaleString()}`} />
          <Field label="Owner" value={campaign.owner_name} />
          <Field label="Region" value={campaign.region} />
        </div>
      </div>

      <h3 className="mt-8 mb-4 text-lg font-semibold">Health Snapshots</h3>

      {snapshots.length === 0 ? (
        <p className="text-sm text-muted-foreground">No health data available.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Date</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Impressions</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Clicks</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">CTR</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Viewability</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Spend</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Pacing</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Anomaly</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.map((s) => (
                <tr key={s.id} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="px-4 py-3">{fmtDate(s.snapshot_at)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{s.impressions?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{s.clicks?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{pct(s.ctr)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{pct(s.viewability)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">${s.spend_usd?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{pct(s.budget_pacing_pct)}</td>
                  <td className="px-4 py-3">
                    {s.anomaly_flag ? (
                      <Badge variant="destructive" title={s.anomaly_reason}>
                        {s.anomaly_reason || 'Anomaly'}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TODO [Step 5 — Day 1 / Module 05 — Workflow Deep Dive]: Add an investigations list section.
          Display existing investigations for this campaign with their status, question,
          owner, and severity. Each investigation should be clickable for detail view. */}

      {/* TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Add investigation status
          progression UI. */}

      {/* TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Add an AI usage card or
          recommendation note section on the investigation detail view. */}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <span className="font-medium text-muted-foreground">{label}</span>
      <span className="mt-0.5 block">{value || '-'}</span>
    </div>
  );
}

function fmtDate(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString();
}

function pct(value) {
  if (value == null) return '-';
  return `${value.toFixed(1)}%`;
}

const STATUS_STYLES = {
  Active: 'bg-green-50 text-green-700',
  Paused: 'bg-amber-50 text-amber-700',
  Completed: 'bg-gray-100 text-gray-600',
};
const DEFAULT_STATUS_STYLE = 'bg-gray-100 text-gray-600';

function StatusBadge({ status }) {
  return (
    <Badge className={`font-medium ${STATUS_STYLES[status] || DEFAULT_STATUS_STYLE}`}>
      {status}
    </Badge>
  );
}
