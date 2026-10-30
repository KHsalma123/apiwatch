import { Outlet } from "react-router-dom";
import { Logo } from "./AppLayout";

export default function AuthLayout() {
  return (
    <div className="grid min-h-full lg:grid-cols-[1fr_28rem]">
      <section className="hidden bg-ink-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Logo />
        <div>
          <p className="max-w-md text-3xl font-semibold leading-snug">Know your API is down before your users do.</p>
          <p className="mt-4 max-w-md text-ink-400">Add an endpoint, pick an interval, and APIWatch records every response, opens an incident when it fails and closes it when it recovers.</p>
          <div className="mt-10 flex h-10 items-end gap-[3px]" aria-hidden="true">
            {Array.from({ length: 48 }).map((_, i) => (
              <span key={i} className={`h-full w-[5px] rounded-[2px] ${[17, 18, 33].includes(i) ? "bg-alarm" : "bg-signal-glow"}`} />
            ))}
          </div>
        </div>
        <p className="text-sm text-ink-400">Uptime and response-time monitoring for public APIs.</p>
      </section>
      <main className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden"><Logo dark={false} /></div>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
