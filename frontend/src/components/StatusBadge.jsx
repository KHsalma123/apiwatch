const STYLES = {
  UP: { label: "Up", cls: "bg-signal-soft text-signal", dot: "bg-signal live-dot" },
  DOWN: { label: "Down", cls: "bg-alarm-soft text-alarm", dot: "bg-alarm" },
  PENDING: { label: "Pending", cls: "bg-slate-100 text-ink-600", dot: "bg-ink-400" },
  PAUSED: { label: "Paused", cls: "bg-amber-soft text-amber", dot: "bg-amber" },
  OPEN: { label: "Open", cls: "bg-alarm-soft text-alarm", dot: "bg-alarm" },
  RESOLVED: { label: "Resolved", cls: "bg-signal-soft text-signal", dot: "bg-signal" },
};

/** Status is always shown as text + dot (never color alone). */
export default function StatusBadge({ status, paused = false }) {
  const key = paused ? "PAUSED" : status;
  const s = STYLES[key] || STYLES.PENDING;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.cls}`}>
      <span className={`h-2 w-2 rounded-full ${s.dot}`} aria-hidden="true" />
      {s.label}
    </span>
  );
}
