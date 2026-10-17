import { useEffect, useRef, useState } from "react";
import App from "./App";
import { ApiError, apiGet, apiSend, setCsrfToken } from "./lib/api";
import type { Staff, StaffSession } from "./lib/api";

export default function StaffAccess() {
  const [staff, setStaff] = useState<Staff | null>(null);
  const [checking, setChecking] = useState(true);
  const [starting, setStarting] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const sessionChannel = useRef<BroadcastChannel | null>(null);

  useEffect(() => {
    let active = true;
    function expired() {
      setStaff(null);
      setCsrfToken(null);
      setPassword("");
    }
    window.addEventListener("staff-session-expired", expired);
    if (typeof BroadcastChannel !== "undefined") {
      sessionChannel.current = new BroadcastChannel("kings-grillz-staff-session");
      sessionChannel.current.onmessage = event => { if (event.data === "signed-out") expired(); };
    }

    async function checkSession() {
      const delays = [0, 3000, 6000, 10000];
      for (let attempt = 0; attempt < delays.length; attempt++) {
        if (!active) return;
        if (attempt > 0) {
          setStarting(true);
          await new Promise(resolve => setTimeout(resolve, delays[attempt]));
          if (!active) return;
        }
        try {
          const session = await apiGet<StaffSession>("/api/auth/me");
          if (active) { setCsrfToken(session.csrf_token); setStaff(session.staff); }
          return;
        } catch (err) {
          if (!active) return;
          if (err instanceof ApiError && err.status === 401) return;
          if (attempt === delays.length - 1) {
            setError("Cannot reach the staff service. Check the server and try signing in again.");
          }
        }
      }
    }

    void checkSession().finally(() => { if (active) { setChecking(false); setStarting(false); } });
    return () => {
      active = false;
      window.removeEventListener("staff-session-expired", expired);
      sessionChannel.current?.close();
      sessionChannel.current = null;
    };
  }, []);

  useEffect(() => {
    if (!staff) return;
    // Clear customer data from the screen after local inactivity; server expiry is independent.
    let timer: ReturnType<typeof setTimeout>;
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        setStaff(null);
        setCsrfToken(null);
        setError("Your screen was locked after inactivity. Please sign in again.");
      }, 30 * 60 * 1000);
    };
    reset();
    window.addEventListener("pointerdown", reset);
    window.addEventListener("keydown", reset);
    return () => { clearTimeout(timer); window.removeEventListener("pointerdown", reset); window.removeEventListener("keydown", reset); };
  }, [staff]);

  async function signIn(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const session = await apiSend<StaffSession>("/api/auth/login", "POST", { username, password });
      setCsrfToken(session.csrf_token);
      setStaff(session.staff);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setPassword("");
      pending.current = false;
      setBusy(false);
    }
  }

  async function signOut() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await apiSend<void>("/api/auth/logout", "POST", {});
      sessionChannel.current?.postMessage("signed-out");
      setCsrfToken(null);
      setStaff(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-out failed. Please try again.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  if (checking) return <main className="staff-access"><p role="status">{starting ? "Starting the staff service… this can take up to 30 seconds on first load." : "Checking staff session…"}</p></main>;
  if (staff) return <>
    <div className="staff-session-bar">
      <span>Signed in as <strong>{staff.username}</strong> · {staff.role}</span>
      <button type="button" disabled={busy} onClick={() => void signOut()}>{busy ? "Signing out…" : "Sign out"}</button>
      {error && <p role="alert">{error}</p>}
    </div>
    <App key={staff.id} staff={staff} />
  </>;
  return <main className="staff-access">
    <form className="staff-login" onSubmit={signIn}>
      <img src="/logo.png" alt="KING'S GRILLZ" style={{width: 96, height: 96, margin: "0 auto 1rem", display: "block"}} />
      <span className="eyebrow">KING'S GRILLZ SMARTPOS</span>
      <h1>Staff sign-in</h1>
      <p>Use your assigned staff account to manage orders.</p>
      <label>Username<input autoComplete="username" required maxLength={64} value={username} onChange={event => setUsername(event.target.value)} disabled={busy} /></label>
      <label>Password<input type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={event => setPassword(event.target.value)} disabled={busy} /></label>
      {error && <p className="payment-error" role="alert">{error}</p>}
      <button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      <small>Contact your administrator if you need an account or password reset.</small>
    </form>
  </main>;
}
