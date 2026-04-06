import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCampaign, createInvestigation, getInvestigations } from '../api/client';
import { Badge } from '@/components/ui/badge';

// TODO [Step 10 — Day 2 / Module 03 — Parallel Execution]: Import updateInvestigationStatus
//   from '../api/client' for the status progression UI.

// TODO [Step 12 — Day 2 / Module 05 — Production Rollout]: Import getAiRuns from '../api/client'
//   for the AI usage card on the investigation detail view.

export default function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [investigations, setInvestigations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    issue_type: '',
    severity: 'Medium',
    owner_name: '',
    question: '',
    hypothesis: '',
    next_action: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    Promise.all([getCampaign(id), getInvestigations(id)])
      .then(([campaignData, investigationsData]) => {
        if (!stale) {
          setCampaign(campaignData);
          setInvestigations(investigationsData);
          setError(null);
        }
      })
      .catch((err) => {
        if (!stale) {
          setError(err.message);
          setCampaign(null);
          setInvestigations([]);
        }
      })
      .finally(() => { if (!stale) setLoading(false); });
    return () => { stale = true; };
  }, [id]);

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateInvestigation = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const newInv = await createInvestigation({ ...formData, campaign_id: id });
      setInvestigations((prev) => [newInv, ...prev]);
      setShowForm(false);
      setFormData({ issue_type: '', severity: 'Medium', owner_name: '', question: '', hypothesis: '', next_action: '' });
    } catch (err) {
      alert(`Failed to create investigation: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

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
          <StyledBadge value={campaign.status} styles={STATUS_STYLES} />
          {campaign.needs_help && <Badge variant="destructive">Needs Help</Badge>}
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          onClick={() => setShowForm(true)}
        >
          Start Investigation
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreateInvestigation} className="mt-4 rounded-lg border p-6 space-y-4">
          <h3 className="text-lg font-semibold">New Investigation</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-muted-foreground">Issue Type</label>
              <input
                name="issue_type"
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                value={formData.issue_type}
                onChange={handleFormChange}
                placeholder="e.g. Low CTR, Underdelivery"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground">Severity</label>
              <select
                name="severity"
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                value={formData.severity}
                onChange={handleFormChange}
              >
                <option>Critical</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground">Owner</label>
              <input
                name="owner_name"
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                value={formData.owner_name}
                onChange={handleFormChange}
                placeholder="Your name"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground">Question</label>
            <textarea
              name="question"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              rows={2}
              value={formData.question}
              onChange={handleFormChange}
              placeholder="What are we trying to find out?"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground">Hypothesis</label>
            <textarea
              name="hypothesis"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              rows={2}
              value={formData.hypothesis}
              onChange={handleFormChange}
              placeholder="What do we think is causing this?"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground">Next Action</label>
            <textarea
              name="next_action"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              rows={2}
              value={formData.next_action}
              onChange={handleFormChange}
              placeholder="What should we do first?"
              required
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Investigation'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

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

      <h3 className="mt-8 mb-4 text-lg font-semibold">
        Investigations{' '}
        {investigations.length > 0 && (
          <span className="text-sm font-normal text-muted-foreground">({investigations.length})</span>
        )}
      </h3>

      {investigations.length === 0 ? (
        <p className="text-sm text-muted-foreground">No investigations yet.</p>
      ) : (
        <div className="space-y-3">
          {investigations.map((inv) => (
            <div key={inv.id} className="rounded-lg border p-4">
              <div className="flex items-center gap-2 mb-2">
                <StyledBadge value={inv.status} styles={INVESTIGATION_STATUS_STYLES} />
                <StyledBadge value={inv.severity} styles={SEVERITY_STYLES} />
                <span className="text-xs text-muted-foreground ml-auto">{fmtDate(inv.opened_at)}</span>
              </div>
              <p className="text-sm font-medium">{inv.question}</p>
              <p className="text-sm text-muted-foreground mt-1">{inv.hypothesis}</p>
              {inv.owner_name && (
                <p className="text-xs text-muted-foreground mt-2">Owner: {inv.owner_name}</p>
              )}
            </div>
          ))}
        </div>
      )}

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

const DEFAULT_BADGE_STYLE = 'bg-gray-100 text-gray-600';

function StyledBadge({ value, styles }) {
  return (
    <Badge className={`font-medium ${styles[value] || DEFAULT_BADGE_STYLE}`}>
      {value}
    </Badge>
  );
}

const STATUS_STYLES = {
  Active: 'bg-green-50 text-green-700',
  Paused: 'bg-amber-50 text-amber-700',
  Completed: 'bg-gray-100 text-gray-600',
};

const INVESTIGATION_STATUS_STYLES = {
  New: 'bg-blue-50 text-blue-700',
  Investigating: 'bg-amber-50 text-amber-700',
  'Needs Action': 'bg-red-50 text-red-700',
  Resolved: 'bg-green-50 text-green-700',
};

const SEVERITY_STYLES = {
  Critical: 'bg-red-100 text-red-800',
  High: 'bg-orange-50 text-orange-700',
  Medium: 'bg-amber-50 text-amber-700',
  Low: 'bg-gray-100 text-gray-600',
};
