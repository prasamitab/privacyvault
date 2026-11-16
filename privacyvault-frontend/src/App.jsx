import { useEffect, useState } from "react";
import { Fingerprint } from "lucide-react";
import RealHEDemo from "./RealHEDemo";
import api, { BACKEND_URL } from "./api";
import "./workspace.css";

export default function App() {
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    let active = true;

    api.get("/health")
      .then(({ data }) => {
        if (active) {
          setHealth(
            data.status === "healthy" ? "connected" : "reachable"
          );
        }
      })
      .catch(() => {
        if (active) setHealth("unavailable");
      });

    return () => {
      active = false;
    };
  }, []);

  const status = {
    checking: "Checking API",
    connected: "API connected",
    reachable: "API reachable",
    unavailable: "API unavailable",
  }[health];

  return (
    <main className="pv-app">
      <div className="pv-shell">
        <header className="pv-header">
          <a className="pv-brand" href="#workspace">
            <Fingerprint size={25} aria-hidden="true" />
            PrivacyVault
          </a>

          <span className={`pv-status pv-status--${health}`} role="status">
            <span aria-hidden="true" />
            {status}
          </span>
        </header>

        <section className="pv-intro">
          <p className="pv-eyebrow">A LITTLE LESS EXPOSURE.</p>
          <h1>
            Payroll insights.
            <br />
            <em>Without the exposure.</em>
          </h1>
          <p>
            Calculate totals from encrypted payroll data.
            <br className="pv-desktop-break" />
            Keep the key on your machine.
          </p>
        </section>

        <div id="workspace">
          <RealHEDemo />
        </div>

        <details className="pv-sample">
          <summary>
            <span>Example dataset</span>
            <span>NYC payroll · 2025 · 25 records</span>
          </summary>

          <div className="pv-detail-copy">
            <p>
              Regular gross pay from a prepared sample of
              DEPT OF ED PEDAGOGICAL records, measured in USD.
              This description does not identify your uploaded file.
            </p>
            <p>
              The importer selected the latest eligible fiscal year
              at retrieval time, the agency with the most eligible
              records, then the first 25 eligible rows ordered by
              source row ID. Eligibility required positive regular
              pay, nonnegative overtime, and supported input values.
            </p>
            <p>
              This is a non-random public-data sample—not an
              agency-wide total or a live feed. Names were not
              requested; public records may still be linkable.
            </p>
            <a
              href="https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e"
              target="_blank"
              rel="noreferrer"
            >
              View NYC Open Data source ↗
            </a>
          </div>
        </details>

        <ol className="pv-workflow" aria-label="Computation workflow">
          <li><span>01</span> Upload encrypted data</li>
          <li><span>02</span> Compute remotely</li>
          <li><span>03</span> Verify locally</li>
        </ol>

        <footer className="pv-footer">
          <p>PrivacyVault · Educational demo</p>

          <details>
            <summary>Privacy & limitations</summary>
            <div className="pv-detail-copy">
              <p>
                Upload only the encrypted dataset—not your CSV,
                local reference, verification report, or secret key.
                Ciphertexts, record counts, and public-file
                identifiers are sent to the API.
              </p>
              <p>
                Decryption happens separately on the key holder’s
                machine. The mean is derived locally from the
                decrypted sum and record count.
              </p>
              <p>
                Receiving a result does not verify it. Numerical
                agreement is not a cryptographic proof of server
                execution or result authenticity.
              </p>
              <p>
                Public data demonstrates the workflow, not secrecy
                of its source values. A key holder given individual
                ciphertexts could decrypt them.
              </p>
              <p>
                API connectivity is not an end-to-end encryption
                test. This prototype is not production payroll software.
              </p>
              <p className="pv-mono">Configured API: {BACKEND_URL}</p>
            </div>
          </details>
        </footer>
      </div>
    </main>
  );
}