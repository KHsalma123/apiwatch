import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ErrorBanner } from "../components/Feedback";
import { btn, input, label } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../services/api";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate(location.state?.from || "/", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <h1 className="text-2xl font-semibold">Log in</h1>
      <ErrorBanner message={error} />
      <div>
        <label className={label} htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" required className={input} value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div>
        <label className={label} htmlFor="password">Password</label>
        <input id="password" type="password" autoComplete="current-password" required className={input} value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      <button type="submit" className={`${btn.primary} w-full`} disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      <p className="text-sm text-ink-600">No account yet? <Link to="/register" className={btn.link}>Create one</Link></p>
    </form>
  );
}
