import { useState } from "react";
import { Link } from "react-router-dom";
import { AvailabilityChart, HistoryChart, RangeSelect, ResponseTimeChart } from "../components/Charts";
import { EmptyState, ErrorBanner, Loading } from "../components/Feedback";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { btn, panel } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { dashboardApi } from "../services/apiwatch";
import { formatDateTime, formatDuration, formatMs, formatPct, timeAgo } from "../utils/format";

function Headline({ s }) {
  if (s.total_monitors === 0) return null;
  const down = s.down;
  const tone = down > 0 ? "border-alarm/40 bg-alarm-soft text-alarm" : s.up > 0 ? "border-signal/30 bg-signal-soft text-signal" : "border-line bg-white text-ink-600";
  const text =
    down > 0 ? `${down} ${down === 1 ? "API is" : "APIs are"} down` : s.up > 0 ? "All monitored APIs are up" : "Waiting for the first checks";
  return (
    <div className={`rounded-lg border px-5 py-4 ${tone}`} role="status">
      <p className="text-lg font-semibold">{text}</p>
      <p className="text-sm opacity-80">
        {s.up} up · {s.down} down{s.pending ? ` · ${s.pending} pending` : ""}{s.paused ? ` · ${s.paused} paused` : ""}
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [range, setRange] = useState("24h");
  const summary = useFetch(() => dashboardApi.summary(), [], { refreshMs: 30000 });
  const charts = useFetch(() => dashboardApi.charts(range), [range], { refreshMs: 60000 });

  if (summary.loading) return <Loading />;
  if (summary.error) return <ErrorBanner message={summary.error} onRetry={summary.reload} />;
  const s = summary.data;

  if (s.total_monitors === 0) {
    return (
      <>
        <h1 className="mb-6 text-2xl font-semibold">Dashboard</h1>
        <EmptyState
          title="You are not monitoring any API yet"
          text="Add your first endpoint and APIWatch starts checking it within a few seconds."
          action={<Link to="/monitors/new" className={btn.primary}>Add a monitor</Link>}
        />
      </>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <Link to="/monitors/new" className={btn.primary}>Add a monitor</Link>
      </div>

      <Headline s={s} />

      <dl className={`${panel} grid grid-cols-2 divide-line sm:grid-cols-3 lg:grid-cols-5 lg:divide-x [&>div]:border-b [&>div]:border-line lg:[&>div]:border-b-0`}>
        <StatCard label="Monitored APIs" value={s.total_monitors} />
        <StatCard label="Up" value={s.up} tone="good" />
        <StatCard label="Down" value={s.down} tone={s.down ? "bad" : "default"} />
        <StatCard label="Avg response" value={formatMs(s.avg_response_time_ms)} hint="last 24 hours" />
        <StatCard label="Uptime" value={formatPct(s.uptime_percentage)} hint="last 24 hours" />
      </dl>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trends</h2>
        <RangeSelect value={range} onChange={setRange} />
      </div>
      {charts.error ? (
        <ErrorBanner message={charts.error} onRetry={charts.reload} />
      ) : charts.loading ? (
        <Loading label="Loading charts…" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <ResponseTimeChart data={charts.data} range={range} />
          <AvailabilityChart data={charts.data} range={range} />
          <div className="lg:col-span-2"><HistoryChart data={charts.data} range={range} /></div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className={panel} aria-labelledby="overview-title">
          <h2 id="overview-title" className="border-b border-line px-5 py-3 font-semibold">API status</h2>
          <ul className="divide-y divide-line">
            {s.monitors.map((m) => (
              <li key={m.id}>
                <Link to={`/monitors/${m.id}`} className="flex items-center justify-between gap-3 px-5 py-3 hover:bg-paper">
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{m.name}</span>
                    <span className="block text-xs text-ink-400">{formatMs(m.last_response_time_ms)} · {timeAgo(m.last_checked_at)}</span>
                  </span>
                  <StatusBadge status={m.last_status} paused={!m.is_active} />
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className={panel} aria-labelledby="incidents-title">
          <div className="flex items-center justify-between border-b border-line px-5 py-3">
            <h2 id="incidents-title" className="font-semibold">Recent incidents</h2>
            <Link to="/incidents" className={btn.link}>View all</Link>
          </div>
          {s.recent_incidents.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-ink-400">No incidents so far.</p>
          ) : (
            <ul className="divide-y divide-line">
              {s.recent_incidents.map((i) => (
                <li key={i.id} className="flex items-center justify-between gap-3 px-5 py-3">
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{i.monitor_name}</span>
                    <span className="block text-xs text-ink-400">{formatDateTime(i.started_at)}{i.duration_seconds != null && ` · lasted ${formatDuration(i.duration_seconds)}`}</span>
                  </span>
                  <StatusBadge status={i.status} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
