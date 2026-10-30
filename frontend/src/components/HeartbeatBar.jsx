import { formatDateTime, formatMs } from "../utils/format";

/** One tick per recent check: green = up, red = down. Oldest on the left. */
export default function HeartbeatBar({ results = [], max = 60 }) {
  const ticks = [...results].slice(0, max).reverse();
  if (ticks.length === 0) return <p className="text-sm text-ink-400">No checks yet.</p>;
  return (
    <div
      className="flex h-9 items-end gap-[3px]"
      role="img"
      aria-label={`Last ${ticks.length} checks: ${ticks.filter((t) => t.status === "UP").length} up, ${ticks.filter((t) => t.status === "DOWN").length} down`}
    >
      {ticks.map((t) => (
        <span
          key={t.id}
          title={`${t.status} – ${formatDateTime(t.checked_at)}${t.response_time_ms != null ? ` – ${formatMs(t.response_time_ms)}` : ""}`}
          className={`h-full min-w-[4px] flex-1 rounded-[2px] ${t.status === "UP" ? "bg-signal-glow" : "bg-alarm"}`}
          style={{ maxWidth: 10 }}
        />
      ))}
    </div>
  );
}
