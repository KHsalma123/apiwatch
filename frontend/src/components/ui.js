// Shared Tailwind class strings so buttons and inputs look the same everywhere.
export const btn = {
  primary: "inline-flex items-center justify-center gap-2 rounded-md bg-steel px-4 py-2 text-sm font-semibold text-white hover:bg-steel-dark disabled:cursor-not-allowed disabled:opacity-60",
  secondary: "inline-flex items-center justify-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink-800 hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60",
  danger: "inline-flex items-center justify-center gap-2 rounded-md bg-alarm px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60",
  link: "text-sm font-semibold text-steel hover:underline",
};
export const input =
  "block w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink-900 placeholder:text-ink-400 focus:border-steel";
export const label = "mb-1 block text-sm font-medium text-ink-800";
export const panel = "rounded-lg border border-line bg-white";
