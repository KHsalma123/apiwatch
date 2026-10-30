import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const axis = { fontSize: 12, fill: "#7d939f" };

export const RANGES = [
  { value: "1h", label: "1 hour" },
  { value: "24h", label: "24 hours" },
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
];

function tick(range) {
  return (iso) => {
    const d = new Date(iso);
    return range === "7d" || range === "30d"
      ? d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
      : d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  };
}

function ChartBox({ title, description, empty, children }) {
  return (
    <figure className="rounded-lg border border-line bg-white p-4">
      <figcaption className="mb-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="text-xs text-ink-400">{description}</p>
      </figcaption>
      <div className="h-56">
        {empty ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-400">No data in this period yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>
        )}
      </div>
    </figure>
  );
}

const tooltipStyle = { borderRadius: 8, border: "1px solid #d9e2df", fontSize: 12 };

export function ResponseTimeChart({ data, range }) {
  return (
    <ChartBox title="Response time" description="Average of successful checks, in milliseconds" empty={!data?.length}>
      <AreaChart data={data} margin={{ left: -10, right: 8, top: 4 }}>
        <CartesianGrid stroke="#e6ecea" vertical={false} />
        <XAxis dataKey="t" tickFormatter={tick(range)} tick={axis} tickLine={false} axisLine={false} minTickGap={32} />
        <YAxis tick={axis} tickLine={false} axisLine={false} unit=" ms" />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v) => [`${v} ms`, "Response time"]} />
        <Area type="monotone" dataKey="avg_response_time_ms" stroke="#0e6377" strokeWidth={2} fill="#0e6377" fillOpacity={0.12} connectNulls />
      </AreaChart>
    </ChartBox>
  );
}

export function AvailabilityChart({ data, range }) {
  return (
    <ChartBox title="Availability" description="Share of checks that were up" empty={!data?.length}>
      <AreaChart data={data} margin={{ left: -10, right: 8, top: 4 }}>
        <CartesianGrid stroke="#e6ecea" vertical={false} />
        <XAxis dataKey="t" tickFormatter={tick(range)} tick={axis} tickLine={false} axisLine={false} minTickGap={32} />
        <YAxis domain={[0, 100]} tick={axis} tickLine={false} axisLine={false} unit="%" />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v) => [`${v}%`, "Availability"]} />
        <Area type="stepAfter" dataKey="uptime_percentage" stroke="#14805a" strokeWidth={2} fill="#2fd08e" fillOpacity={0.18} />
      </AreaChart>
    </ChartBox>
  );
}

export function HistoryChart({ data, range }) {
  return (
    <ChartBox title="Monitoring history" description="Number of checks performed" empty={!data?.length}>
      <BarChart data={data} margin={{ left: -10, right: 8, top: 4 }}>
        <CartesianGrid stroke="#e6ecea" vertical={false} />
        <XAxis dataKey="t" tickFormatter={tick(range)} tick={axis} tickLine={false} axisLine={false} minTickGap={32} />
        <YAxis tick={axis} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v) => [v, "Checks"]} />
        <Bar dataKey="checks" fill="#46606f" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ChartBox>
  );
}

export function RangeSelect({ value, onChange }) {
  return (
    <div role="group" aria-label="Time range" className="inline-flex rounded-md border border-line bg-white p-0.5">
      {RANGES.map((r) => (
        <button
          key={r.value}
          onClick={() => onChange(r.value)}
          aria-pressed={value === r.value}
          className={`rounded px-3 py-1 text-sm font-medium ${value === r.value ? "bg-ink-900 text-white" : "text-ink-600 hover:bg-paper"}`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}
