import { useEffect, useState } from "react";
import RealHEDemo from "./RealHEDemo";
import api, { BACKEND_URL } from "./api";

const card =
  "rounded-2xl border border-white/10 bg-slate-950/60 p-6";

const stages = [
  {
    title: "1. Prepare locally",
    text: "Select and validate salary values from a documented CSV source.",
  },
  {
    title: "2. Encrypt locally",
    text: "Use the existing public key. Keep the CSV and secret key on the owner's machine.",
  },
  {
    title: "3. Compute remotely",
    text: "Upload ciphertexts and request an encrypted sum from the evaluator.",
  },
  {
    title: "4. Verify locally",
    text: "Download the result, decrypt locally, and compare it with a trusted reference.",
  },
];

export default function App() {
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    let active = true;

    api.get("/health")
      .then(({ data }) => {
        if (active) {
          setHealth(
            data.status === "healthy" ? "healthy" : "reachable"
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

  const healthLabel = {
    checking: "Checking backend",
    healthy: "Backend health check passed",
    reachable: "Backend reachable",
    unavailable: "Backend health check unavailable",
  }[health];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10">
        <div className="mx-auto max-w-7xl px-5 py-6">
          <p className="text-sm font-semibold uppercase tracking-widest text-emerald-300">
            PrivacyVault
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Verifiable Encrypted Salary Analytics
          </h1>

          <p className="mt-3 max-w-3xl leading-7 text-slate-300">
            A privacy-preserving computation playground:
            encrypt locally, aggregate ciphertexts remotely,
            and check the decrypted aggregate locally.
          </p>

          <div
            role="status"
            className="mt-5 rounded-xl border border-white/10 bg-white/5 p-4"
          >
            <p className="text-sm">{healthLabel}</p>

            <p className="mt-2 break-all font-mono text-xs text-slate-400">
              Configured API: {BACKEND_URL}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              A health response is not an end-to-end encryption
              or verification test.
            </p>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-8 px-5 py-8">
        <section aria-labelledby="workflow-heading">
          <h2
            id="workflow-heading"
            className="mb-4 text-xl font-semibold"
          >
            The computation workflow
          </h2>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {stages.map((stage) => (
              <article key={stage.title} className={card}>
                <h3 className="font-semibold text-emerald-300">
                  {stage.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">
                  {stage.text}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className={card} aria-labelledby="dataset-heading">
  <p className="text-xs uppercase tracking-widest text-cyan-300">
    Documented public-payroll experiment
  </p>

  <h2
    id="dataset-heading"
    className="mt-2 text-2xl font-semibold"
  >
    Confidential Payroll Analytics
  </h2>

  <p className="mt-3 leading-7 text-slate-300">
    Use case: a payroll owner delegates an aggregate calculation
    to an external service without sending readable individual
    pay values or the secret key.
  </p>

  <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
    <div>
      <dt className="text-slate-400">Demonstration source</dt>
      <dd className="mt-1">NYC Citywide Payroll Data</dd>
    </div>

    <div>
      <dt className="text-slate-400">Fiscal year</dt>
      <dd className="mt-1">2025</dd>
    </div>

    <div>
      <dt className="text-slate-400">Selected agency</dt>
      <dd className="mt-1">DEPT OF ED PEDAGOGICAL</dd>
    </div>

    <div>
      <dt className="text-slate-400">Prepared sample</dt>
      <dd className="mt-1">25 payroll records · USD</dd>
    </div>

    <div>
      <dt className="text-slate-400">Metric</dt>
      <dd className="mt-1">Regular gross paid during the fiscal year</dd>
    </div>

    <div>
      <dt className="text-slate-400">Computation</dt>
      <dd className="mt-1">
        Encrypted sum; mean derived locally after decryption
      </dd>
    </div>
  </dl>

  <p className="mt-5 text-sm leading-6 text-slate-400">
    Selection: latest fiscal year with eligible named-agency
    records at retrieval time, then the agency with the most
    eligible records, then the first 25 eligible rows ordered
    by source row ID. Positive regular pay and nonnegative
    overtime were required.
  </p>

  <p className="mt-3 text-sm leading-6 text-amber-200">
    This is a non-random public-data sample, not an agency-wide
    payroll total or a live feed. Names were not requested.
    Omitting names does not guarantee that public records
    cannot be linked back to their source.
  </p>

  <p className="mt-3 text-sm leading-6 text-slate-400">
    This panel documents the prepared example. It does not
    automatically identify, authenticate, or verify an
    arbitrary uploaded file.
  </p>
</section>
          
        <section aria-labelledby="compute-heading">
          <h2
            id="compute-heading"
            className="mb-3 text-2xl font-semibold"
          >
            Encrypted computation workspace
          </h2>

          <p className="mb-5 text-sm leading-6 text-slate-400">
            Use the uploaded-dataset option for the real-world
            experiment. Upload encrypted-dataset.json only—not
            the original CSV, local reference, or secret key.
          </p>

          <RealHEDemo />
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <article className={card}>
            <h2 className="text-xl font-semibold text-emerald-300">
              Privacy boundary
            </h2>

            <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-6 text-slate-300">
              <li>
                Local preparation uses public cryptographic files
                to encrypt the salary values.
              </li>
              <li>
                The encrypted upload includes ciphertexts,
                a public record count, and public-file identifiers.
              </li>
              <li>
                The separate local verifier uses the secret key
                to decrypt the returned aggregate.
              </li>
              <li>
                The mean is calculated locally by dividing the
                decrypted sum by the public record count.
              </li>
            </ul>
          </article>

          <article className={card}>
            <h2 className="text-xl font-semibold text-amber-300">
              Evidence and limitations
            </h2>

            <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-6 text-slate-300">
              <li>
                Check numerical consistency using the separate
                local verifier and a preselected tolerance.
              </li>
              <li>
                The website does not mark an experiment verified
                merely because an API request succeeded.
              </li>
              <li>
                A passing numerical check is not a cryptographic
                proof of server execution or result authenticity.
              </li>
              <li>
                Public source data demonstrates the workflow;
                it does not establish secrecy of those source values.
              </li>
            </ul>
          </article>
        </section>

        <footer className="border-t border-white/10 py-6 text-center text-xs leading-6 text-slate-500">
          PrivacyVault · Educational CKKS demonstration ·
          Local key-holder verification · Not production payroll software
        </footer>
      </div>
    </main>
  );
}