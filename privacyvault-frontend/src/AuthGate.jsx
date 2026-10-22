import { useState } from "react";
import api, { BACKEND_URL } from "./api";
import App from "./App.jsx";

export default function AuthGate() {
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function login(event) {
    event.preventDefault();
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
        <div className="flex items-center justify-between gap-4 bg-slate-900 px-5 py-3 text-sm text-slate-200">
          <span>PrivacyVault demo · Signed in as {username}</span>
          <button
            type="button"
            onClick={logout}
            className="rounded-lg border border-white/20 px-4 py-2 hover:bg-white/10"
          >
            Sign out
          </button>
        </div>
        <App />
      </>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-5 text-white">
      <form
        onSubmit={login}
        className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-xl"
      >
        <h1 className="text-2xl font-bold">PrivacyVault demo</h1>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          Sign in with the demo access credentials. This is not your
          GitHub or Render account login.
        </p>

        <label htmlFor="demo-username" className="mt-6 block text-sm">
          Username
        </label>
        <input
          id="demo-username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          disabled={busy}
          required
          className="mt-2 w-full rounded-lg border border-white/20 bg-slate-950 p-3"
        />

        <label htmlFor="demo-password" className="mt-4 block text-sm">
          Password
        </label>
        <input
          id="demo-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={busy}
          required
          className="mt-2 w-full rounded-lg border border-white/20 bg-slate-950 p-3"
        />

        {error && (
          <p role="alert" className="mt-4 text-sm text-red-300">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="mt-6 w-full rounded-lg bg-cyan-300 p-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Connecting — first request may take a minute…" : "Sign in"}
        </button>

        <p className="mt-4 text-xs leading-5 text-slate-400">
          Credentials stay in page memory until sign-out or refresh.
          Your browser may separately offer to save them.
          Never enter or upload your HE secret key.
        </p>

        <p className="mt-3 break-all text-xs text-slate-500">
          API: {BACKEND_URL}
        </p>
      </form>
    </main>
  );
}
