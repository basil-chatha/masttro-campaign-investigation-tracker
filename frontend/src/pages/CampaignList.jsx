import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCampaigns } from '../api/client';

export default function CampaignList() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCampaigns()
      .then((data) => { setCampaigns(data); setError(null); })
      .catch((err) => { setError(err.message); setCampaigns([]); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Loading campaigns…</p>;
  if (error) return <p className="text-destructive">Error: {error}</p>;

  // TODO [Step 1 — Day 1 / Module 01 — First Win]: Make one tiny, visible change to the campaign list.
  //   Examples: add a health badge column, surface a delivery note, show an anomaly flag,
  //   or display an extra evidence field. The goal is a bounded first win the room can
  //   verify instantly. Use plan mode first to inspect the repo, then make the change.
  //   Re-run the app and review the diff before moving on.

  return (
    <div>
      <h2 className="mb-6 text-2xl font-semibold">Campaigns</h2>

      <div className="overflow-hidden rounded-lg border">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Code</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Advertiser</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Objective</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Channel</th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">Budget</th>
              {/* TODO [Step 1 — Day 1 / Module 01 — First Win]: Add a new <th> here for the
                  health badge, delivery note, or anomaly indicator column. This is the
                  "one small UI change" that demonstrates Claude's first bounded win. */}
            </tr>
          </thead>
          <tbody>
            {campaigns.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                  No campaigns found.
                </td>
              </tr>
            ) : campaigns.map((c) => (
              <tr key={c.id} className="border-b last:border-0 hover:bg-muted/50">
                <td className="px-4 py-3">
                  <Link to={`/campaigns/${c.id}`} className="font-medium text-primary underline-offset-4 hover:underline">
                    {c.campaign_code}
                  </Link>
                </td>
                <td className="px-4 py-3">{c.name}</td>
                <td className="px-4 py-3 text-muted-foreground">{c.advertiser}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={c.status} />
                </td>
                <td className="px-4 py-3">{c.objective}</td>
                <td className="px-4 py-3">{c.channel}</td>
                <td className="px-4 py-3 text-right tabular-nums">
                  ${c.budget_usd?.toLocaleString()}
                </td>
                {/* TODO [Step 1 — Day 1 / Module 01 — First Win]: Add a new <td> here
                    to display the health badge, delivery note, or anomaly indicator
                    for each campaign row. This may require extending the backend
                    CampaignOut schema or adding a joined query. */}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const STATUS_STYLES = {
  Active: 'bg-green-50 text-green-700',
  Paused: 'bg-amber-50 text-amber-700',
  Completed: 'bg-gray-100 text-gray-600',
};
const DEFAULT_STATUS_STYLE = 'bg-gray-100 text-gray-600';

function StatusBadge({ status }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status] || DEFAULT_STATUS_STYLE}`}>
      {status}
    </span>
  );
}
