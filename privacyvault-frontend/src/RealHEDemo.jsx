import { useState } from "react";
import axios from "axios";
import api, { BACKEND_URL } from "./api";

const MAX_FILE_BYTES = 64 * 1024 * 1024;
const HASH_PATTERN = /^[a-f0-9]{64}$/i;

function prepareUpload(dataset) {
  if (
    !dataset ||
    typeof dataset !== "object" ||
    Array.isArray(dataset) ||
    dataset.format_version !== 1 ||
    dataset.scheme !== "CKKS" ||
    dataset.operation !== "sum" ||
    !Number.isInteger(dataset.employee_count) ||
    dataset.employee_count < 1 ||
    dataset.employee_count > 100 ||
    !Array.isArray(dataset.ciphertexts_base64) ||
    dataset.ciphertexts_base64.length !== dataset.employee_count ||
    !dataset.ciphertexts_base64.every(
      (value) => typeof value === "string" && value.length > 0
    ) ||
    typeof dataset.context_sha256 !== "string" ||
    !HASH_PATTERN.test(dataset.context_sha256) ||
    typeof dataset.public_key_sha256 !== "string" ||
    !HASH_PATTERN.test(dataset.public_key_sha256)
  ) {
    throw new Error(
      "Select encrypted-dataset.json created by encrypt_csv.py " +
      "or encrypt_dataset.py—not a result, reference, or key file."
    );
  }

  return {
    format_version: 1,
    scheme: "CKKS",
    operation: "sum",
    employee_count: dataset.employee_count,
    context_sha256: dataset.context_sha256,
    public_key_sha256: dataset.public_key_sha256,
    ciphertexts_base64: dataset.ciphertexts_base64,
  };
}

function validateResult(data, upload) {
  if (
    !data ||
    data.mode !== "real-he-uploaded-dataset-demo" ||
    data.scheme !== "CKKS" ||
    data.operation !== "sum" ||
    data.employee_count !== upload.employee_count ||
    data.context_sha256 !== upload.context_sha256 ||
    data.public_key_sha256 !== upload.public_key_sha256 ||
    data.secret_key_loaded !== false ||
    data.decryption_performed !== false ||
    typeof data.encrypted_result_base64 !== "string" ||
    !data.encrypted_result_base64 ||
    !Number.isInteger(data.ciphertext_size_bytes) ||
    data.ciphertext_size_bytes <= 0 ||
    !Number.isFinite(data.computation_time_ms) ||
    data.computation_time_ms < 0
  ) {
    throw new Error(
      "The API returned unexpected result metadata. " +
      "Do not treat this response as verified."
    );
  }
}

export default function RealHEDemo() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function handleFileChange(event) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(null);
    setResult(null);
    setMetrics(null);
    setError("");

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Choose an encrypted dataset JSON file.");
      event.target.value = "";
      return;
    }

    if (file.size === 0 || file.size > MAX_FILE_BYTES) {
      setError("Choose a non-empty JSON file no larger than 64 MiB.");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  }

  async function runAggregation() {
    if (busy || !selectedFile) return;

    setBusy(true);
    setError("");
    setResult(null);
    setMetrics(null);

    try {
      let parsed;

      try {
        parsed = JSON.parse(await selectedFile.text());
      } catch {
        throw new Error("The selected file could not be read as JSON.");
      }

      const upload = prepareUpload(parsed);
      const body = JSON.stringify(upload);
      const requestBytes = new Blob([body]).size;

      if (requestBytes > MAX_FILE_BYTES) {
        throw new Error("The prepared upload exceeds 64 MiB.");
      }

      const started = performance.now();

      const response = await api.post(
        "/api/v1/real-he/aggregate-upload",
        body,
        {
          headers: { "Content-Type": "application/json" },
          timeout: 120000,
        }
      );

      const requestElapsedMs = performance.now() - started;

      validateResult(response.data, upload);

      setResult(response.data);
      setMetrics({
        requestBytes,
        requestElapsedMs,
      });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (requestError.code === "ECONNABORTED") {
        setError(
          "The request timed out. Check the configured backend " +
          "and evaluator service, then retry."
        );
      } else if (axios.isAxiosError(requestError)) {
        setError(
          "The API request failed. Check your login, configured " +
          "API address, and backend status."
        );
      } else {
        setError(requestError.message || "Could not process the dataset.");
      }
    } finally {
      setBusy(false);
    }
  }

  function downloadEncryptedResult() {
    if (!result) return;

    const exportData = {
      mode: result.mode,
      scheme: result.scheme,
      operation: result.operation,
      employee_count: result.employee_count,
      ciphertext_size_bytes: result.ciphertext_size_bytes,
      computation_time_ms: result.computation_time_ms,
      encrypted_result_base64: result.encrypted_result_base64,
      context_sha256: result.context_sha256,
      public_key_sha256: result.public_key_sha256,
      secret_key_loaded: result.secret_key_loaded,
      decryption_performed: result.decryption_performed,
      client_observation: {
        api_base_url: BACKEND_URL,
        downloaded_at: new Date().toISOString(),
        request_elapsed_ms: metrics?.requestElapsedMs,
        request_bytes: metrics?.requestBytes,
        note: "Client-recorded metadata, not independently attested.",
      },
    };

    const blob = new Blob(
      [JSON.stringify(exportData, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "privacyvault-uploaded-result.json";

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <section
      aria-busy={busy}
      className="rounded-2xl border border-cyan-300/30 bg-slate-950/60 p-6"
    >
      <p className="text-xs uppercase tracking-widest text-cyan-300">
        CKKS encrypted-sum experiment
      </p>

      <h3 className="mt-2 text-xl font-semibold text-white">
        Upload ciphertexts, receive ciphertext
      </h3>

      <p className="mt-3 text-sm leading-6 text-slate-300">
        The evaluator adds the uploaded ciphertexts. Decryption and
        comparison with the plaintext reference happen separately
        on the key holder's machine.
      </p>

      <div className="mt-5 rounded-xl border border-white/10 p-4">
        <label
          htmlFor="he-dataset-file"
          className="block text-sm font-semibold"
        >
          Encrypted dataset JSON
        </label>

        <p
          id="he-dataset-help"
          className="mt-2 text-xs leading-5 text-slate-400"
        >
          Supports 1–100 records and a maximum file size of 64 MiB.
          Select encrypted-dataset.json only. Never select your
          CSV, local reference, verification report, or secret key.
        </p>

        <input
          id="he-dataset-file"
          type="file"
          accept=".json,application/json"
          onChange={handleFileChange}
          disabled={busy}
          aria-describedby="he-dataset-help"
          className="mt-4 block w-full rounded-lg border border-white/15 p-3 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-white disabled:opacity-50"
        />

        {selectedFile && (
          <p className="mt-3 break-all text-xs text-slate-400">
            Selected: {selectedFile.name} ·{" "}
            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MiB
          </p>
        )}

        <button
          type="button"
          onClick={runAggregation}
          disabled={busy || !selectedFile}
          className="mt-4 rounded-xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy
            ? "Computing encrypted sum..."
            : "Aggregate uploaded dataset"}
        </button>
      </div>

      {busy && (
        <p role="status" className="mt-4 text-sm text-cyan-200">
          Waiting for the API response. No decryption is performed here.
        </p>
      )}

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-6 rounded-xl border border-white/10 p-5">
          <p role="status" className="font-semibold text-cyan-200">
            Encrypted aggregate received
          </p>

          <p className="mt-2 text-sm text-amber-200">
            Local numerical verification is still required.
          </p>

          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-slate-400">Record count</dt>
              <dd className="mt-1">{result.employee_count}</dd>
            </div>

            <div>
              <dt className="text-xs text-slate-400">
                Server-reported processing time
              </dt>
              <dd className="mt-1">
                {result.computation_time_ms.toFixed(2)} ms
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-400">
                Browser-observed request duration
              </dt>
              <dd className="mt-1">
                {metrics.requestElapsedMs.toFixed(2)} ms
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-400">
                Request body size
              </dt>
              <dd className="mt-1">
                {metrics.requestBytes.toLocaleString()} bytes
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-400">
                Result ciphertext size
              </dt>
              <dd className="mt-1">
                {result.ciphertext_size_bytes.toLocaleString()} bytes
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-400">Operation</dt>
              <dd className="mt-1">Encrypted sum · CKKS</dd>
            </div>
          </dl>

          <p className="mt-5 text-xs leading-5 text-slate-400">
            Request duration includes the API round trip, not local
            encryption or decryption. Response checks validate expected
            metadata; they do not prove correct server execution.
          </p>

          <details className="mt-5 text-xs">
            <summary className="cursor-pointer text-slate-300">
              Public-file identifiers and ciphertext preview
            </summary>

            <div className="mt-3 space-y-3 break-all font-mono text-slate-400">
              <p>Context SHA-256: {result.context_sha256}</p>
              <p>Public key SHA-256: {result.public_key_sha256}</p>
              <p>
                Ciphertext preview:{" "}
                {result.encrypted_result_base64.slice(0, 80)}…
              </p>
            </div>
          </details>

          <button
            type="button"
            onClick={downloadEncryptedResult}
            className="mt-5 rounded-xl border border-white/20 px-5 py-3 text-sm font-semibold hover:bg-white/5"
          >
            Download encrypted result
          </button>

          <p className="mt-3 text-xs leading-5 text-slate-400">
            The download contains aggregate ciphertext, API metadata,
            and client-recorded request information—not the plaintext
            total or secret key. Run the separate local verifier next.
          </p>
        </div>
      )}
    </section>
  );
}