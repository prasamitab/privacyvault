import { useState } from "react";
import axios from "axios";
import api from "./api";

const BACKEND_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const API_BASE = `${BACKEND_URL}/api/v1/real-he`;

const MAX_FILE_BYTES = 64 * 1024 * 1024;

export default function RealHEDemo() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);

  const busy = loading !== "";

  function handleFileChange(event) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(null);
    setError("");
    setResult(null);

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Select the encrypted-dataset.json file.");
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

  async function runAggregation(mode) {
    if (busy) return;

    if (mode === "upload" && !selectedFile) {
      setError("Select an encrypted dataset first.");
      return;
    }

    setLoading(mode);
    setError("");
    setResult(null);

    try {
      let response;

      if (mode === "upload") {
        const text = await selectedFile.text();

        let dataset;

        try {
          dataset = JSON.parse(text);
        } catch {
          throw new Error("The selected file is not valid JSON.");
        }

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
          typeof dataset.public_key_sha256 !== "string"
        ) {
          throw new Error(
            "Choose the encrypted dataset created by encrypt_dataset.py, " +
              "not a result file or key file."
          );
        }

        response = await api.post(
          `${API_BASE}/aggregate-upload`,
          text,
          {
            headers: {
              "Content-Type": "application/json",
            },
            timeout: 120000,
          }
        );
      } else {
        response = await api.post(
          `${API_BASE}/aggregate-demo`,
          undefined,
          { timeout: 120000 }
        );
      }

      setResult(response.data);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (requestError.code === "ECONNABORTED") {
        setError(
          "The request timed out. Check the backend and Docker HE service."
        );
      } else if (!axios.isAxiosError(requestError)) {
        setError(requestError.message || "Could not read the dataset.");
      } else {
        setError(
          "Request failed. Check the backend and Docker HE service."
        );
      }
    } finally {
      setLoading("");
    }
  }

  function downloadEncryptedResult() {
    if (!result?.encrypted_result_base64) return;

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
    };

    const blob = new Blob(
      [JSON.stringify(exportData, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download =
      result.mode === "real-he-uploaded-dataset-demo"
        ? "privacyvault-uploaded-result.json"
        : "privacyvault-encrypted-result.json";

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  const uploadedResult =
    result?.mode === "real-he-uploaded-dataset-demo";

  return (
    <section
      aria-busy={busy}
      className="mb-8 rounded-2xl border border-cyan-300/30 bg-slate-950/60 p-6"
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">
        Real homomorphic encryption • CKKS
      </p>

      <h2 className="mt-2 text-2xl font-bold text-white">
        Encrypted aggregation lab
      </h2>

      <p className="mt-3 text-sm leading-6 text-slate-300">
        Upload a dataset encrypted by your local Python tool, or run
        the fixed two-record demo. The evaluator adds ciphertexts;
        decryption stays in the separate key-holder workflow.
      </p>

      <p className="mt-2 text-xs text-slate-400">
        Local educational demo • Separate from the mock employee form
      </p>

      <div className="mt-6 rounded-xl border border-white/10 p-4">
        <label
          htmlFor="he-dataset-file"
          className="block text-sm font-semibold text-white"
        >
          Encrypted dataset
        </label>

        <p
          id="he-dataset-help"
          className="mt-1 text-xs leading-5 text-slate-400"
        >
          Choose encrypted-dataset.json. Up to 100 records and 64 MiB.
          Do not select key files or plaintext salary files.
        </p>

        <input
          id="he-dataset-file"
          type="file"
          accept=".json,application/json"
          onChange={handleFileChange}
          disabled={busy}
          aria-describedby="he-dataset-help"
          className="mt-3 block w-full rounded-lg border border-white/15 p-2 text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-sm file:text-white disabled:opacity-50"
        />

        {selectedFile && (
          <p className="mt-2 break-all text-xs text-slate-400">
            Selected: {selectedFile.name} ·{" "}
            {(selectedFile.size / 1024).toFixed(1)} KiB
          </p>
        )}

        <button
          type="button"
          onClick={() => runAggregation("upload")}
          disabled={busy || !selectedFile}
          className="mt-4 rounded-xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading === "upload"
            ? "Aggregating encrypted records..."
            : "Aggregate uploaded dataset"}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => runAggregation("demo")}
          disabled={busy}
          className="rounded-xl border border-white/15 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading === "demo"
            ? "Running fixed demo..."
            : "Run fixed two-record demo"}
        </button>

        <span className="text-xs text-slate-400">
          No upload needed for the fixed demo.
        </span>
      </div>

      {busy && (
        <p role="status" className="mt-4 text-sm text-cyan-200">
          Waiting for the encrypted aggregate…
        </p>
      )}

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div
          role="status"
          className="mt-5 rounded-xl border border-white/10 bg-black/20 p-4"
        >
          <p className="font-semibold text-emerald-300">
            Encrypted aggregate received
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {uploadedResult
              ? "Source: uploaded encrypted dataset"
              : "Source: fixed fictional dataset"}
          </p>

          <dl className="mt-5 grid grid-cols-2 gap-5 text-sm lg:grid-cols-4">
            <div>
              <dt className="text-slate-400">Scheme</dt>
              <dd className="mt-1 text-white">{result.scheme}</dd>
            </div>

            <div>
              <dt className="text-slate-400">
                {uploadedResult
                  ? "Uploaded records"
                  : "Fixed-dataset records"}
              </dt>
              <dd className="mt-1 text-white">
                {result.employee_count}
              </dd>
            </div>

            <div>
              <dt className="text-slate-400">Ciphertext size</dt>
              <dd className="mt-1 text-white">
                {Number(result.ciphertext_size_bytes).toLocaleString()}{" "}
                bytes
              </dd>
            </div>

            <div>
              <dt className="text-slate-400">Evaluator processing time</dt>
              <dd className="mt-1 text-white">
                {Number(result.computation_time_ms).toFixed(2)} ms
              </dd>
            </div>
          </dl>

          <p className="mt-4 text-sm text-cyan-200">
            No plaintext total is returned. Download this result and
            verify it separately using the matching key-holder files.
          </p>

          <code className="mt-4 block break-all rounded-lg bg-black/30 p-3 text-xs text-emerald-200">
            {result.encrypted_result_preview}
          </code>

          <button
            type="button"
            onClick={downloadEncryptedResult}
            disabled={!result.encrypted_result_base64}
            className="mt-4 rounded-xl border border-white/15 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10 disabled:opacity-50"
          >
            Download encrypted result
          </button>

          <p className="mt-3 text-xs text-slate-400">
            Exports aggregate ciphertext and metadata only. The
            download does not include a private key or plaintext total.
          </p>
        </div>
      )}
    </section>
  );
}