export default function StatCard({ label, value, hint, tone = "default" }) {
  const color = tone === "bad" ? "text-alarm" : tone === "good" ? "text-signal" : "text-ink-900";
  return (
    <div className="px-5 py-4">
      <dt className="text-sm text-ink-600">{label}</dt>
      <dd className={`mt-1 text-2xl font-semibold tabular-nums ${color}`}>{value}</dd>
      {hint && <p className="mt-0.5 text-xs text-ink-400">{hint}</p>}
    </div>
  );
}
