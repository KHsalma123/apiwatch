export function Loading({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-600" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-line border-t-steel" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div role="alert" className="flex items-start justify-between gap-4 rounded-lg border border-alarm/30 bg-alarm-soft px-4 py-3 text-sm text-alarm">
      <span>{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="shrink-0 font-semibold underline underline-offset-2">
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, text, action }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed border-line bg-white px-6 py-14 text-center">
      <h3 className="text-base font-semibold text-ink-900">{title}</h3>
      {text && <p className="mt-1 max-w-sm text-sm text-ink-600">{text}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
