"""
PrivacyVault real-HE evaluation service.

Local demonstration only:
- Loads a fixed test dataset containing CKKS ciphertexts.
- Does not load a secret key.
- Returns an encrypted aggregate, never a plaintext salary.
- Does not implement authentication or aggregate-release policy.
"""

import base64
import json
import time
from pathlib import Path
import hashlib

from fastapi import FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from Pyfhel import Pyfhel, PyCtxt


PUBLIC = Path("/public")

app = FastAPI(
    title="PrivacyVault HE Evaluator",
    description=(
        "Real CKKS addition on a fixed encrypted demonstration dataset. "
        "No secret key is loaded."
    ),
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "scheme": "CKKS",
        "mode": "real-he-fixed-dataset-demo",
        "context_available": (PUBLIC / "context.bin").is_file(),
        "secret_key_loaded": False,
    }


@app.post("/aggregate")
def aggregate():
    if Path("/private").exists():
        raise HTTPException(
            status_code=500,
            detail="Private directory must not be mounted in this service",
        )

    started = time.perf_counter()

    try:
        manifest = json.loads(
            (PUBLIC / "manifest.json").read_text(encoding="utf-8")
        )

        filenames = manifest["files"]
        count = manifest["count"]

        if (
            not isinstance(filenames, list)
            or not filenames
            or len(filenames) > 100
            or not isinstance(count, int)
            or count != len(filenames)
        ):
            raise ValueError("Invalid demonstration manifest")

        for filename in filenames:
            if (
                not isinstance(filename, str)
                or Path(filename).name != filename
                or not filename.endswith(".ctxt")
            ):
                raise ValueError("Invalid ciphertext filename")

        evaluator = Pyfhel()
        evaluator.load_context(str(PUBLIC / "context.bin"))

        ciphertexts = [
            PyCtxt(
                pyfhel=evaluator,
                fileName=str(PUBLIC / filename),
            )
            for filename in filenames
        ]

        encrypted_total = ciphertexts[0]

        for ciphertext in ciphertexts[1:]:
            encrypted_total = encrypted_total + ciphertext

        result_bytes = encrypted_total.to_bytes()

        return {
            "scheme": "CKKS",
            "operation": "sum",
            "employee_count": count,
            "encrypted_result_base64": base64.b64encode(
                result_bytes
            ).decode("ascii"),
            "ciphertext_size_bytes": len(result_bytes),
            "computation_time_ms": (
                time.perf_counter() - started
            ) * 1000,
            "secret_key_loaded": False,
            "dataset": "fixed-encrypted-test-files",
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Encrypted aggregation failed. Check the mounted "
                "context, manifest, and ciphertext files."
            ),
        )
MAX_UPLOAD_BYTES = 64 * 1024 * 1024
MAX_CIPHERTEXT_BYTES = 1024 * 1024
MAX_BASE64_CHARS = 4 * ((MAX_CIPHERTEXT_BYTES + 2) // 3)


def evaluate_uploaded_dataset(dataset):
    if Path("/private").exists():
        raise HTTPException(
            status_code=500,
            detail="Private directory must not be mounted.",
        )

    if not isinstance(dataset, dict):
        raise HTTPException(
            status_code=400,
            detail="Expected a JSON object.",
        )

    if (
        type(dataset.get("format_version")) is not int
        or dataset["format_version"] != 1
        or dataset.get("scheme") != "CKKS"
        or dataset.get("operation") != "sum"
    ):
        raise HTTPException(
            status_code=400,
            detail="Expected format version 1, CKKS, and sum.",
        )

    count = dataset.get("employee_count")
    ciphertexts = dataset.get("ciphertexts_base64")

    if (
        type(count) is not int
        or not 1 <= count <= 100
        or not isinstance(ciphertexts, list)
        or len(ciphertexts) != count
    ):
        raise HTTPException(
            status_code=400,
            detail="Expected 1–100 ciphertexts and a matching count.",
        )

    try:
        context_hash = hashlib.sha256(
            (PUBLIC / "context.bin").read_bytes()
        ).hexdigest()

        public_key_hash = hashlib.sha256(
            (PUBLIC / "public.key").read_bytes()
        ).hexdigest()
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Evaluator public files are unavailable.",
        )

    if (
        dataset.get("context_sha256") != context_hash
        or dataset.get("public_key_sha256") != public_key_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Dataset identifiers do not match this evaluator.",
        )

    started = time.perf_counter()

    try:
        evaluator = Pyfhel()
        evaluator.load_context(str(PUBLIC / "context.bin"))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Evaluator context could not be loaded.",
        )

    try:
        encrypted_total = None

        for encoded in ciphertexts:
            if (
                not isinstance(encoded, str)
                or not encoded
                or len(encoded) > MAX_BASE64_CHARS
            ):
                raise ValueError("Invalid ciphertext field")

            ciphertext_bytes = base64.b64decode(
                encoded,
                validate=True,
            )

            if not 0 < len(ciphertext_bytes) <= MAX_CIPHERTEXT_BYTES:
                raise ValueError("Invalid ciphertext size")

            ciphertext = PyCtxt(
                pyfhel=evaluator,
                bytestring=ciphertext_bytes,
            )

            if encrypted_total is None:
                encrypted_total = ciphertext
            else:
                encrypted_total = encrypted_total + ciphertext

        result_bytes = encrypted_total.to_bytes()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ciphertexts could not be loaded or added. "
                "Use compatible files from the local encryption tool."
            ),
        )

    return {
        "mode": "real-he-uploaded-dataset-demo",
        "scheme": "CKKS",
        "operation": "sum",
        "employee_count": count,
        "encrypted_result_base64": base64.b64encode(
            result_bytes
        ).decode("ascii"),
        "ciphertext_size_bytes": len(result_bytes),
        "computation_time_ms": (
            time.perf_counter() - started
        ) * 1000,
        "context_sha256": context_hash,
        "public_key_sha256": public_key_hash,
        "secret_key_loaded": False,
        "decryption_performed": False,
        "dataset": "uploaded-encrypted-records",
    }


@app.post("/aggregate-upload")
async def aggregate_upload(request: Request):
    media_type = request.headers.get(
        "content-type", ""
    ).split(";")[0].strip().lower()

    if media_type != "application/json":
        raise HTTPException(
            status_code=415,
            detail="Send the encrypted dataset as application/json.",
        )

    body = bytearray()

    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Encrypted dataset exceeds the 64 MiB limit.",
            )
        body.extend(chunk)

    try:
        dataset = json.loads(body)
    except (ValueError, RecursionError):
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON dataset.",
        )

    return await run_in_threadpool(
        evaluate_uploaded_dataset,
        dataset,
    )