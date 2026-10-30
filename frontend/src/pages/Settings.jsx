import { useState } from "react";
import { ErrorBanner } from "../components/Feedback";
import { btn, input, label, panel } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../services/api";
import { authApi } from "../services/apiwatch";

function ProfileForm() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null); setSaved(false);
    try {
      setUser(await authApi.updateMe({ name, email }));
      setSaved(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className={`${panel} space-y-4 p-6`}>
      <h2 className="text-lg font-semibold">Profile</h2>
      <ErrorBanner message={error} />
      {saved && <p role="status" className="rounded-md bg-signal-soft px-4 py-2 text-sm text-signal">Profile saved.</p>}
      <div><label className={label} htmlFor="p-name">Name</label><input id="p-name" className={input} value={name} onChange={(e) => setName(e.target.value)} required /></div>
      <div><label className={label} htmlFor="p-email">Email</label><input id="p-email" type="email" className={input} value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
      <button className={btn.primary} disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
    </form>
  );
}

function PasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(null); setSaved(false);
    if (next.length < 8) return setError("The new password must have at least 8 characters.");
    setBusy(true);
    try {
      await authApi.changePassword({ current_password: current, new_password: next });
      setSaved(true); setCurrent(""); setNext("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className={`${panel} space-y-4 p-6`}>
      <h2 className="text-lg font-semibold">Change password</h2>
      <ErrorBanner message={error} />
      {saved && <p role="status" className="rounded-md bg-signal-soft px-4 py-2 text-sm text-signal">Password changed.</p>}
      <div><label className={label} htmlFor="cur">Current password</label><input id="cur" type="password" autoComplete="current-password" className={input} value={current} onChange={(e) => setCurrent(e.target.value)} required /></div>
      <div><label className={label} htmlFor="new">New password</label><input id="new" type="password" autoComplete="new-password" className={input} value={next} onChange={(e) => setNext(e.target.value)} required /></div>
      <button className={btn.primary} disabled={busy}>{busy ? "Saving…" : "Change password"}</button>
    </form>
  );
}

export default function Settings() {
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <ProfileForm />
      <PasswordForm />
    </div>
  );
}
