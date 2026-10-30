import { useState } from "react";
import { errorMessage } from "../services/api";
import { INTERVAL_OPTIONS } from "../utils/format";
import { ErrorBanner } from "./Feedback";
import { btn, input, label } from "./ui";

const EMPTY = { name: "", url: "https://", method: "GET", interval_seconds: 60, timeout_seconds: 10, expected: "", is_active: true };

function parseCodes(text) {
  const parts = text.split(/[,\s]+/).filter(Boolean);
  const codes = parts.map(Number);
  if (codes.some((c) => !Number.isInteger(c) || c < 100 || c > 599)) return null;
  return codes;
}

export default function MonitorForm({ initial, submitLabel, onSubmit, onCancel }) {
  const [form, setForm] = useState(
    initial ? { ...EMPTY, ...initial, expected: (initial.expected_status_codes || []).join(", ") } : EMPTY
  );
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    const codes = parseCodes(form.expected);
    if (codes === null) return setError("Expected status codes must be numbers between 100 and 599, separated by commas.");
    setSaving(true);
    try {
      await onSubmit({
        name: form.name.trim(),
        url: form.url.trim(),
        method: form.method,
        interval_seconds: Number(form.interval_seconds),
        timeout_seconds: Number(form.timeout_seconds),
        expected_status_codes: codes,
        is_active: form.is_active,
      });
    } catch (err) {
      setError(errorMessage(err));
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      <ErrorBanner message={error} />
      <div>
        <label className={label} htmlFor="name">Name</label>
        <input id="name" className={input} value={form.name} onChange={set("name")} maxLength={100} required placeholder="Payments API" />
      </div>
      <div className="grid gap-5 sm:grid-cols-[8rem_1fr]">
        <div>
          <label className={label} htmlFor="method">Method</label>
          <select id="method" className={input} value={form.method} onChange={set("method")}>
            {["GET", "POST", "PUT", "DELETE"].map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className={label} htmlFor="url">URL</label>
          <input id="url" type="url" className={`${input} font-mono`} value={form.url} onChange={set("url")} required placeholder="https://api.example.com/health" />
        </div>
      </div>
      <p className="-mt-2 text-xs text-ink-400">Public http(s) addresses only. Localhost and private networks are blocked.</p>
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label className={label} htmlFor="interval">Check every</label>
          <select id="interval" className={input} value={form.interval_seconds} onChange={set("interval_seconds")}>
            {INTERVAL_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className={label} htmlFor="timeout">Timeout (seconds)</label>
          <input id="timeout" type="number" min={1} max={30} className={input} value={form.timeout_seconds} onChange={set("timeout_seconds")} />
        </div>
      </div>
      <div>
        <label className={label} htmlFor="expected">Expected status codes <span className="font-normal text-ink-400">(optional)</span></label>
        <input id="expected" className={input} value={form.expected} onChange={set("expected")} placeholder="200, 204" />
        <p className="mt-1 text-xs text-ink-400">Leave empty to accept any 2xx response.</p>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={form.is_active} onChange={set("is_active")} className="h-4 w-4 accent-[#0e6377]" />
        Start monitoring right away
      </label>
      <div className="flex justify-end gap-3 border-t border-line pt-5">
        <button type="button" className={btn.secondary} onClick={onCancel}>Cancel</button>
        <button type="submit" className={btn.primary} disabled={saving}>{saving ? "Saving…" : submitLabel}</button>
      </div>
    </form>
  );
}
