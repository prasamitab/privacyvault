import { useState } from "react";
import { Fingerprint, ArrowRight, LogOut } from "lucide-react";
import api, { BACKEND_URL } from "./api";
import App from "./App.jsx";
import "./workspace.css";

export default function AuthGate() {
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function login(event) {
    event.preventDefault();

    if (busy) return;

    setBusy(true);
    setError("");

    const auth = { username, password };

    try {
      await api.get("/", {
        auth,
        timeout: 120000,
      });

      api.defaults.auth = auth;
      setPassword("");
      setAuthenticated(true);
    } catch (requestError) {
      if (requestError.response?.status === 401) {
        setError("Incorrect username or password.");
      } else {
        setError(
          "Could not reach the API. It may be waking up, or its CORS " +
          "settings may not allow this website. Wait and try again."
        );
      }
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    delete api.defaults.auth;
    setAuthenticated(false);
    setPassword("");
    setError("");
  }

  if (authenticated) {
    return (
      <>
        <div className="pv-session">
          <div className="pv-session-inner">
            <p>
              Demo workspace
              <span className="pv-session-divider" aria-hidden="true">
                /
              </span>
              <span className="pv-session-user">
                Signed in as {username}
              </span>
            </p>

            <button
              type="button"
              onClick={logout}
              className="pv-signout"
            >
              Sign out
              <LogOut size={14} aria-hidden="true" />
            </button>
          </div>
        </div>

        <App />
      </>
    );
  }

  return (
    <main className="pv-app pv-auth-page">
      <div className="pv-auth-shell">
        <header className="pv-auth-header">
          <a className="pv-brand" href="#demo-signin">
            <Fingerprint size={25} aria-hidden="true" />
            PrivacyVault
          </a>
          <span className="pv-auth-demo-label">DEMO ACCESS</span>
        </header>

        <div className="pv-auth-content">
          <section
            className="pv-auth-intro"
            aria-labelledby="pv-auth-title"
          >
            <p className="pv-eyebrow">PRIVATE COMPUTATION.</p>
            <h1 id="pv-auth-title">
              The insights.
              <br />
              <em>Not the exposure.</em>
            </h1>
            <p>
              Explore encrypted payroll analytics.
              Keep decryption on your machine.
            </p>
          </section>

          <form
            id="demo-signin"
            className="pv-auth-card"
            onSubmit={login}
            aria-labelledby="pv-signin-title"
          >
            <div className="pv-auth-card-heading">
              <h2 id="pv-signin-title">Welcome to the demo</h2>
              <p>Sign in with your demo access credentials.</p>
            </div>

            <div className="pv-auth-field">
              <label htmlFor="demo-username">Username</label>
              <input
                id="demo-username"
                name="username"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={busy}
                required
              />
            </div>

            <div className="pv-auth-field">
              <label htmlFor="demo-password">Password</label>
              <input
                id="demo-password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={busy}
                aria-describedby="pv-auth-credential-help"
                required
              />
            </div>

            <p id="pv-auth-credential-help" className="pv-auth-hint">
              Use the project’s demo credentials—not your GitHub
              or Render password.
            </p>

            {error && (
              <div role="alert" className="pv-error">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="pv-primary-button pv-auth-submit"
            >
              {busy ? "Connecting…" : "Enter workspace"}
              <ArrowRight size={17} aria-hidden="true" />
            </button>

            {busy && (
              <p role="status" className="pv-feedback">
                Connecting to the API. The first request may take
                a minute while the service wakes up.
              </p>
            )}

            <p className="pv-auth-key-note">
              Your HE secret key is never needed to sign in.
            </p>

            <details className="pv-auth-details">
              <summary>About demo access</summary>
              <div className="pv-detail-copy">
                <p>
                  Credentials are held in this page’s memory until
                  sign-out or refresh. Your browser may separately
                  offer to save them.
                </p>
                <p>
                  Never enter or upload your HE secret key.
                  Decryption and numerical verification happen
                  separately on your machine.
                </p>
                <p className="pv-mono">Configured API: {BACKEND_URL}</p>
              </div>
            </details>
          </form>
        </div>

        <footer className="pv-auth-footer">
          <span>PrivacyVault · Educational demo</span>
          <span>Encrypted computation. Local verification.</span>
        </footer>
      </div>
    </main>
  );
}