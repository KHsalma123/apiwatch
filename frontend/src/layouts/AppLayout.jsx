import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/monitors", label: "Monitors" },
  { to: "/incidents", label: "Incidents" },
  { to: "/settings", label: "Settings" },
];

export function Logo({ dark = true }) {
  return (
    <span className="flex items-center gap-2.5 text-lg font-bold tracking-tight">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill={dark ? "#2fd08e" : "#10202a"} />
        <path d="M4 17h6l3-8 5 15 3-7h7" fill="none" stroke={dark ? "#10202a" : "#2fd08e"} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className={dark ? "text-white" : "text-ink-900"}>APIWatch</span>
    </span>
  );
}

function SideNav({ onNavigate }) {
  return (
    <nav aria-label="Main" className="mt-8 flex flex-col gap-1">
      {NAV.map((n) => (
        <NavLink
          key={n.to}
          to={n.to}
          end={n.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `rounded-md px-3 py-2 text-sm font-medium ${isActive ? "bg-white/10 text-white" : "text-ink-400 hover:bg-white/5 hover:text-white"}`
          }
        >
          {n.label}
        </NavLink>
      ))}
    </nav>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-full">
      {/* Sidebar (desktop) */}
      <aside className="hidden w-60 shrink-0 bg-ink-900 px-4 py-6 lg:block">
        <div className="px-2"><Logo /></div>
        <SideNav />
      </aside>

      {/* Sidebar (mobile drawer) */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-ink-950/50" />
          <aside className="relative h-full w-64 bg-ink-900 px-4 py-6" onClick={(e) => e.stopPropagation()}>
            <div className="px-2"><Logo /></div>
            <SideNav onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-line bg-white px-4 sm:px-6">
          <button className="rounded-md p-2 text-ink-800 hover:bg-paper lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <div className="hidden lg:block" />
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-ink-600 sm:inline">{user?.name}</span>
            <button onClick={handleLogout} className="rounded-md border border-line px-3 py-1.5 text-sm font-medium hover:bg-paper">Log out</button>
          </div>
        </header>
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl"><Outlet /></div>
        </main>
      </div>
    </div>
  );
}
