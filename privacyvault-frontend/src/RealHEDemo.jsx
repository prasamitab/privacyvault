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
      className="pv-calculator"
      aria-labelledby="pv-calculator-title"
    >
      <div className="pv-card-heading">
        <span className="pv-card-mark" aria-hidden="true">∑</span>
        <div>
          <h2 id="pv-calculator-title">Calculate an encrypted total</h2>
          <p>Choose your prepared dataset to begin.</p>
        </div>
      </div>

      <div className="pv-picker">
        <input
          id="he-dataset-file"
          className="pv-file-input"
          type="file"
          accept=".json,application/json"
          onChange={handleFileChange}
          disabled={busy}
          aria-describedby="he-dataset-help"
        />

        <label htmlFor="he-dataset-file" className="pv-file-label">
          <span className="pv-upload-symbol" aria-hidden="true">↑</span>

          <span className="pv-file-title">
            {selectedFile ? selectedFile.name : "Choose encrypted file"}
          </span>

          <span className="pv-file-description">
            {selectedFile
              ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MiB · Click to change`
              : "encrypted-dataset.json · Up to 64 MiB"}
          </span>
        </label>
      </div>

      <p id="he-dataset-help" className="pv-upload-help">
        Supports 1–100 records. Keep your secret key and plaintext CSV local.
      </p>

      <button
        type="button"
        onClick={runAggregation}
        disabled={busy || !selectedFile}
        className="pv-primary-button"
      >
        {busy ? "Calculating encrypted total…" : "Calculate encrypted total"}
        <span aria-hidden="true">{busy ? "…" : "→"}</span>
      </button>

      {busy && (
        <p role="status" className="pv-feedback">
          Waiting for the API. A sleeping service may take a moment.
          No decryption happens here.
        </p>
      )}

      {error && (
        <div role="alert" className="pv-error">
          <p>We couldn’t complete the calculation.</p>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <section className="pv-result" aria-labelledby="pv-result-title">
          <div className="pv-result-heading">
            <h3 id="pv-result-title" role="status">
              Your encrypted result is ready
            </h3>
            <span>Verification pending</span>
          </div>

          <p>
            Download the result, then decrypt and check it using
            your separate local verifier.
          </p>

          <button
            type="button"
            onClick={downloadEncryptedResult}
            className="pv-download-button"
          >
            Download encrypted result
            <span aria-hidden="true">↓</span>
          </button>

          <p className="pv-result-note">
            Contains ciphertext and metadata—not a readable payroll total.
          </p>

          <details className="pv-result-details">
            <summary>Calculation details</summary>

            <dl className="pv-metrics">
              <div>
                <dt>Records</dt>
                <dd>{result.employee_count}</dd>
              </div>
              <div>
                <dt>Operation</dt>
                <dd>Encrypted sum · CKKS</dd>
              </div>
              <div>
                <dt>Server-reported processing time</dt>
                <dd>{result.computation_time_ms.toFixed(2)} ms</dd>
              </div>
              <div>
                <dt>Browser-observed request duration</dt>
                <dd>{metrics.requestElapsedMs.toFixed(2)} ms</dd>
              </div>
              <div>
                <dt>Request body</dt>
                <dd>{metrics.requestBytes.toLocaleString()} bytes</dd>
              </div>
              <div>
                <dt>Result ciphertext</dt>
                <dd>
                  {result.ciphertext_size_bytes.toLocaleString()} bytes
                </dd>
              </div>
            </dl>

            <div className="pv-detail-copy">
              <p>
                Request duration includes the API round trip, not local
                encryption or decryption. Server timing is reported
                by the API, not independently attested.
              </p>
              <p>
                Response checks validate expected metadata. They do
                not prove correct server execution.
              </p>
              <p className="pv-mono">
                Context SHA-256: {result.context_sha256}
              </p>
              <p className="pv-mono">
                Public key SHA-256: {result.public_key_sha256}
              </p>
              <p className="pv-mono">
                Ciphertext preview:{" "}
                {result.encrypted_result_base64.slice(0, 80)}…
              </p>
            </div>
          </details>
        </section>
      )}
    </section>
  );
}