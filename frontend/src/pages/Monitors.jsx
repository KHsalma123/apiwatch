import { useState } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import { EmptyState, ErrorBanner, Loading } from "../components/Feedback";
import StatusBadge from "../components/StatusBadge";
import { btn, input, panel } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { errorMessage } from "../services/api";
import { monitorsApi } from "../services/apiwatch";
import { formatMs, timeAgo } from "../utils/format";

export default function Monitors() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [toDelete, setToDelete] = useState(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);
  const limit = 20;

  const { data, error, loading, reload } = useFetch(
    () => monitorsApi.list({ page, limit, search: search || undefined, status: status || undefined }),
    [page, search, status],
    { refreshMs: 30000 }
  );

  async function toggle(m) {
    setActionError(null);
    try {
      await monitorsApi.setActive(m.id, !m.is_active);
      reload();
    } catch (e) {
      setActionError(errorMessage(e));
    }
  }

  async function confirmDelete() {
    setBusy(true);
    try {
      await monitorsApi.remove(toDelete.id);
      setToDelete(null);
      reload();
    } catch (e) {
      setActionError(errorMessage(e));
      setToDelete(null);
    } finally {
      setBusy(false);
    }
  }

  const noFilters = !search && !status;
  const pages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Monitors</h1>
        <Link to="/monitors/new" className={btn.primary}>Add a monitor</Link>
      </div>

      <div className="flex flex-wrap gap-3">
        <input aria-label="Search monitors" className={`${input} max-w-xs`} placeholder="Search by name" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <select aria-label="Filter by status" className={`${input} max-w-[10rem]`} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="UP">Up</option>
          <option value="DOWN">Down</option>
          <option value="PENDING">Pending</option>
        </select>
      </div>

      <ErrorBanner message={actionError} />
      {loading && !data ? (
        <Loading />
      ) : error ? (
        <ErrorBanner message={error} onRetry={reload} />
      ) : data.items.length === 0 ? (
        noFilters ? (
          <EmptyState title="No monitors yet" text="Add the first API you want to keep an eye on." action={<Link to="/monitors/new" className={btn.primary}>Add a monitor</Link>} />
        ) : (
          <EmptyState title="No monitor matches these filters" text="Try another name or status." />
        )
      ) : (
        <div className={`${panel} overflow-x-auto`}>
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-line text-ink-600">
              <tr>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium">Response</th>
                <th className="px-3 py-3 font-medium">Last check</th>
                <th className="px-5 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.items.map((m) => (
                <tr key={m.id}>
                  <td className="max-w-xs px-5 py-3">
                    <Link to={`/monitors/${m.id}`} className="font-medium text-steel hover:underline">{m.name}</Link>
                    <div className="truncate font-mono text-xs text-ink-400"><span className="mr-1.5 font-semibold">{m.method}</span>{m.url}</div>
                  </td>
                  <td className="px-3 py-3"><StatusBadge status={m.last_status} paused={!m.is_active} /></td>
                  <td className="px-3 py-3 tabular-nums">{formatMs(m.last_response_time_ms)}</td>
                  <td className="px-3 py-3 text-ink-600">{timeAgo(m.last_checked_at)}</td>
                  <td className="whitespace-nowrap px-5 py-3 text-right">
                    <button className={`${btn.link} mr-4`} onClick={() => toggle(m)}>{m.is_active ? "Pause" : "Resume"}</button>
                    <Link className={`${btn.link} mr-4`} to={`/monitors/${m.id}/edit`}>Edit</Link>
                    <button className="text-sm font-semibold text-alarm hover:underline" onClick={() => setToDelete(m)}>Delete</button>
                  </td>
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

      <ConfirmDialog
        open={Boolean(toDelete)}
        title="Delete this monitor?"
        message={toDelete ? `"${toDelete.name}" and all its check history and incidents will be permanently deleted.` : ""}
        confirmLabel="Delete monitor"
        busy={busy}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
