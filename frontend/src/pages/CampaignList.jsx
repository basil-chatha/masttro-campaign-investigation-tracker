import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCampaigns } from '../api/client';
import { Badge } from '@/components/ui/badge';

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
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Health</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">
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
                <td className="px-4 py-3">
                  {c.needs_help ? (
                    <Badge variant="destructive">Needs Help</Badge>
                  ) : (
                    <Badge variant="success">Healthy</Badge>
                  )}
                </td>
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
    <Badge className={`font-medium ${STATUS_STYLES[status] || DEFAULT_STATUS_STYLE}`}>
      {status}
    </Badge>
  );
}
