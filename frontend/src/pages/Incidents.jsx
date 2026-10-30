import { useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorBanner, Loading } from "../components/Feedback";
import StatusBadge from "../components/StatusBadge";
import { btn, input, panel } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { incidentsApi } from "../services/apiwatch";
import { formatDateTime, formatDuration } from "../utils/format";

export default function Incidents() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const limit = 20;
  const { data, error, loading, reload } = useFetch(
    () => incidentsApi.list({ page, limit, status: status || undefined }),
    [page, status],
    { refreshMs: 30000 }
  );
  const pages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Incidents</h1>
        <select aria-label="Filter by status" className={`${input} max-w-[10rem]`} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All incidents</option>
          <option value="OPEN">Open</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      {loading && !data ? <Loading /> : error ? <ErrorBanner message={error} onRetry={reload} /> : data.items.length === 0 ? (
        <EmptyState title={status ? "No incidents with this status" : "No incidents"} text="An incident opens when a monitored API stops responding correctly, and closes when it recovers." />
      ) : (
        <div className={`${panel} overflow-x-auto`}>
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-line text-ink-600">
              <tr><th className="px-5 py-3 font-medium">API</th><th className="px-3 py-3 font-medium">Started</th><th className="px-3 py-3 font-medium">Duration</th><th className="px-3 py-3 font-medium">Status</th><th className="px-5 py-3 font-medium">Error</th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.items.map((i) => (
                <tr key={i.id}>
                  <td className="px-5 py-3"><Link className="font-medium text-steel hover:underline" to={`/monitors/${i.monitor_id}`}>{i.monitor_name || "Monitor"}</Link></td>
                  <td className="whitespace-nowrap px-3 py-3">{formatDateTime(i.started_at)}</td>
                  <td className="px-3 py-3 tabular-nums">{i.duration_seconds != null ? formatDuration(i.duration_seconds) : "ongoing"}</td>
                  <td className="px-3 py-3"><StatusBadge status={i.status} /></td>
                  <td className="px-5 py-3 text-ink-600">{i.error_message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && pages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <button className={btn.secondary} disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span className="text-ink-600">Page {page} of {pages}</span>
          <button className={btn.secondary} disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
