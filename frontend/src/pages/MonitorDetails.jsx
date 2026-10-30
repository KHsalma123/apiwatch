import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AvailabilityChart, RangeSelect, ResponseTimeChart } from "../components/Charts";
import ConfirmDialog from "../components/ConfirmDialog";
import { ErrorBanner, Loading } from "../components/Feedback";
import HeartbeatBar from "../components/HeartbeatBar";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { btn, panel } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { errorMessage } from "../services/api";
import { monitorsApi } from "../services/apiwatch";
import { formatDateTime, formatDuration, formatMs, formatPct, timeAgo } from "../utils/format";

export default function MonitorDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [range, setRange] = useState("24h");
  const [historyPage, setHistoryPage] = useState(1);
  const [checking, setChecking] = useState(false);
  const [notice, setNotice] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const monitor = useFetch(() => monitorsApi.get(id), [id], { refreshMs: 30000 });
  const stats = useFetch(() => monitorsApi.stats(id, range), [id, range], { refreshMs: 30000 });
  const chart = useFetch(() => monitorsApi.chart(id, range), [id, range], { refreshMs: 60000 });
  const recent = useFetch(() => monitorsApi.results(id, { limit: 60 }), [id], { refreshMs: 30000 });
  const history = useFetch(() => monitorsApi.results(id, { page: historyPage, limit: 10 }), [id, historyPage]);
  const incidents = useFetch(() => monitorsApi.incidents(id, { limit: 10 }), [id], { refreshMs: 30000 });

  async function runCheck() {
    setChecking(true);
    setNotice(null);
    try {
      const r = await monitorsApi.check(id);
      setNotice({ ok: r.status === "UP", text: r.status === "UP" ? `Up – HTTP ${r.http_status_code} in ${formatMs(r.response_time_ms)}` : `Down – ${r.error_message}` });
      [monitor, stats, chart, recent, history, incidents].forEach((f) => f.reload());
    } catch (e) {
      setNotice({ ok: false, text: errorMessage(e) });
    } finally {
      setChecking(false);
    }
  }

  async function toggle() {
    try {
      await monitorsApi.setActive(id, !monitor.data.is_active);
      monitor.reload();
    } catch (e) {
      setNotice({ ok: false, text: errorMessage(e) });
    }
  }

  async function remove() {
    try {
      await monitorsApi.remove(id);
      navigate("/monitors");
    } catch (e) {
      setNotice({ ok: false, text: errorMessage(e) });
      setConfirmDelete(false);
    }
  }

  if (monitor.loading) return <Loading />;
  if (monitor.error) return <ErrorBanner message={monitor.error} onRetry={monitor.reload} />;
  const m = monitor.data;
  const st = stats.data;
  const hPages = history.data ? Math.max(1, Math.ceil(history.data.total / 10)) : 1;

  return (
    <div className="space-y-6">
      <Link to="/monitors" className={btn.link}>Back to monitors</Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold">{m.name}</h1>
            <StatusBadge status={m.last_status} paused={!m.is_active} />
          </div>
          <p className="mt-1 break-all font-mono text-sm text-ink-600"><span className="font-semibold">{m.method}</span> {m.url}</p>
          <p className="mt-1 text-xs text-ink-400">Checked every {formatDuration(m.interval_seconds)} · timeout {m.timeout_seconds}s · last check {timeAgo(m.last_checked_at)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className={btn.primary} onClick={runCheck} disabled={checking}>{checking ? "Checking…" : "Check now"}</button>
          <button className={btn.secondary} onClick={toggle}>{m.is_active ? "Pause" : "Resume"}</button>
          <Link className={btn.secondary} to={`/monitors/${id}/edit`}>Edit</Link>
          <button className={btn.secondary} onClick={() => setConfirmDelete(true)}>Delete</button>
        </div>
      </div>

      {notice && (
        <p role="status" className={`rounded-md px-4 py-2 text-sm ${notice.ok ? "bg-signal-soft text-signal" : "bg-alarm-soft text-alarm"}`}>{notice.text}</p>
      )}

      <dl className={`${panel} grid grid-cols-2 lg:grid-cols-4 lg:divide-x lg:divide-line [&>div]:border-b [&>div]:border-line lg:[&>div]:border-b-0`}>
        <StatCard label="HTTP status" value={m.last_http_status_code ?? "–"} hint="latest check" />
        <StatCard label="Latest response" value={formatMs(m.last_response_time_ms)} />
        <StatCard label="Uptime" value={formatPct(st?.uptime_percentage)} hint={`last ${range}`} tone={st?.uptime_percentage != null && st.uptime_percentage < 99 ? "bad" : "good"} />
        <StatCard label="Avg response" value={formatMs(st?.avg_response_time_ms)} hint={st?.max_response_time_ms ? `max ${formatMs(st.max_response_time_ms)}` : `last ${range}`} />
      </dl>

      <section className={`${panel} p-5`} aria-labelledby="hb-title">
        <h2 id="hb-title" className="mb-3 text-sm font-semibold">Last checks</h2>
        {recent.loading ? <Loading label="Loading…" /> : <HeartbeatBar results={recent.data?.items || []} />}
      </section>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Performance</h2>
        <RangeSelect value={range} onChange={setRange} />
      </div>
      {chart.error ? <ErrorBanner message={chart.error} onRetry={chart.reload} /> : (
        <div className="grid gap-4 lg:grid-cols-2">
          <ResponseTimeChart data={chart.data} range={range} />
          <AvailabilityChart data={chart.data} range={range} />
        </div>
      )}

      <section className={panel} aria-labelledby="inc-title">
        <h2 id="inc-title" className="border-b border-line px-5 py-3 font-semibold">Incident history</h2>
        {incidents.data?.items.length ? (
          <ul className="divide-y divide-line">
            {incidents.data.items.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                <span>
                  <span className="font-medium">{formatDateTime(i.started_at)}</span>
                  <span className="block text-xs text-ink-400">{i.error_message}</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className="text-ink-600">{i.duration_seconds != null ? formatDuration(i.duration_seconds) : "ongoing"}</span>
                  <StatusBadge status={i.status} />
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="px-5 py-8 text-center text-sm text-ink-400">No incidents for this monitor.</p>
        )}
      </section>

      <section className={`${panel} overflow-x-auto`} aria-labelledby="hist-title">
        <h2 id="hist-title" className="border-b border-line px-5 py-3 font-semibold">Check history</h2>
        {history.loading && !history.data ? <Loading /> : history.data?.items.length ? (
          <>
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead className="border-b border-line text-ink-600">
                <tr><th className="px-5 py-2 font-medium">Time</th><th className="px-3 py-2 font-medium">Status</th><th className="px-3 py-2 font-medium">HTTP</th><th className="px-3 py-2 font-medium">Response</th><th className="px-5 py-2 font-medium">Error</th></tr>
              </thead>
              <tbody className="divide-y divide-line">
                {history.data.items.map((r) => (
                  <tr key={r.id}>
                    <td className="whitespace-nowrap px-5 py-2">{formatDateTime(r.checked_at)}</td>
                    <td className="px-3 py-2"><StatusBadge status={r.status} /></td>
                    <td className="px-3 py-2 tabular-nums">{r.http_status_code ?? "–"}</td>
                    <td className="px-3 py-2 tabular-nums">{formatMs(r.response_time_ms)}</td>
                    <td className="px-5 py-2 text-ink-600">{r.error_message || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {hPages > 1 && (
              <div className="flex items-center justify-between border-t border-line px-5 py-3 text-sm">
                <button className={btn.secondary} disabled={historyPage <= 1} onClick={() => setHistoryPage((p) => p - 1)}>Newer</button>
                <span className="text-ink-600">Page {historyPage} of {hPages}</span>
                <button className={btn.secondary} disabled={historyPage >= hPages} onClick={() => setHistoryPage((p) => p + 1)}>Older</button>
              </div>
            )}
          </>
        ) : (
          <p className="px-5 py-8 text-center text-sm text-ink-400">No checks yet. The first one runs within a few seconds, or use “Check now”.</p>
        )}
      </section>

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this monitor?"
        message="Its check history and incidents will be permanently deleted."
        confirmLabel="Delete monitor"
        onConfirm={remove}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
