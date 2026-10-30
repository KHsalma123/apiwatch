import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorBanner } from "../components/Feedback";
import { btn, input, label } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../services/api";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    if (form.password.length < 8) return setError("Password must have at least 8 characters.");
    setBusy(true);
    setError(null);
    try {
      await register(form.name, form.email, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <h1 className="text-2xl font-semibold">Create your account</h1>
      <ErrorBanner message={error} />
      <div>
        <label className={label} htmlFor="name">Name</label>
        <input id="name" autoComplete="name" required className={input} value={form.name} onChange={set("name")} />
      </div>
      <div>
        <label className={label} htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" required className={input} value={form.email} onChange={set("email")} />
      </div>
      <div>
        <label className={label} htmlFor="password">Password</label>
        <input id="password" type="password" autoComplete="new-password" required minLength={8} className={input} value={form.password} onChange={set("password")} />
        <p className="mt-1 text-xs text-ink-400">At least 8 characters.</p>
      </div>
      <button type="submit" className={`${btn.primary} w-full`} disabled={busy}>{busy ? "Creating account…" : "Create account"}</button>
      <p className="text-sm text-ink-600">Already registered? <Link to="/login" className={btn.link}>Log in</Link></p>
    </form>
  );
}
