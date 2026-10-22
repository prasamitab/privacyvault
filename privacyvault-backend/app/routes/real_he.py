"""
Bridge to the local Docker-based CKKS evaluator.

This route:
- Uses the fixed encrypted demonstration dataset.
- Does not load secret keys.
- Does not decrypt results.
- Does not use the mock employee database.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from fastapi import Request as FastAPIRequest
from starlette.concurrency import run_in_threadpool
from app.config import settings


from fastapi import APIRouter, HTTPException


router = APIRouter()
logger = logging.getLogger(__name__)

HE_SERVICE_BASE_URL = settings.HE_SERVICE_BASE_URL.rstrip("/")
HE_SERVICE_URL = f"{HE_SERVICE_BASE_URL}/aggregate"


@router.post("/aggregate-demo")
def aggregate_demo():
    request = Request(
        HE_SERVICE_URL,
        data=b"",
        headers={"Accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)

        if (
            result.get("scheme") != "CKKS"
            or result.get("operation") != "sum"
            or not isinstance(
                result.get("encrypted_result_base64"), str
            )
            or not result["encrypted_result_base64"]
        ):
            raise ValueError("Unexpected HE service response")

        ciphertext = result["encrypted_result_base64"]

        return {
            "mode": "real-he-fixed-dataset-demo",
            "scheme": "CKKS",
            "operation": "sum",
            "employee_count": result["employee_count"],
            "ciphertext_size_bytes": result["ciphertext_size_bytes"],
            "computation_time_ms": result["computation_time_ms"],
            "encrypted_result_base64": ciphertext,
            "encrypted_result_preview": ciphertext[:80] + "...",
            "decryption_performed": False,
            "note": (
                "Fixed encrypted test dataset. "
                "Decryption stays in the separate key-holder workflow."
            ),
        }

    except HTTPError:
        logger.exception("HE evaluator returned an HTTP error")
        raise HTTPException(
            status_code=502,
            detail="HE evaluator could not complete aggregation",
        )
    except (URLError, TimeoutError):
        logger.exception("HE evaluator is unavailable")
        raise HTTPException(
            status_code=503,
            detail="HE evaluator unavailable. Check Docker port 8001.",
        )
    except (ValueError, KeyError, TypeError):
        logger.exception("Invalid response from HE evaluator")
        raise HTTPException(
            status_code=502,
            detail="Invalid response from HE evaluator",
        )
HE_UPLOAD_URL = f"{HE_SERVICE_BASE_URL}/aggregate-upload"
MAX_UPLOAD_BYTES = 64 * 1024 * 1024


def forward_encrypted_dataset(body: bytes):
    request = Request(
        HE_UPLOAD_URL,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)

        if not isinstance(result, dict):
            raise ValueError("Expected a response object")

        ciphertext = result.get("encrypted_result_base64")
        count = result.get("employee_count")
        size = result.get("ciphertext_size_bytes")

        if (
            result.get("scheme") != "CKKS"
            or result.get("operation") != "sum"
            or not isinstance(ciphertext, str)
            or not ciphertext
            or type(count) is not int
            or not 1 <= count <= 100
            or type(size) is not int
            or size <= 0
            or result.get("secret_key_loaded") is not False
            or result.get("decryption_performed") is not False
        ):
            raise ValueError("Unexpected HE service response")

        return {
            "mode": "real-he-uploaded-dataset-demo",
            "scheme": "CKKS",
            "operation": "sum",
            "employee_count": count,
            "ciphertext_size_bytes": size,
            "computation_time_ms": result["computation_time_ms"],
            "encrypted_result_base64": ciphertext,
            "encrypted_result_preview": ciphertext[:80] + "...",
            "context_sha256": result["context_sha256"],
            "public_key_sha256": result["public_key_sha256"],
            "secret_key_loaded": False,
            "decryption_performed": False,
            "note": (
                "Uploaded encrypted dataset. "
                "Decryption stays in the separate key-holder workflow."
            ),
        }

    except HTTPError as error:
        if error.code in (400, 413, 415, 422):
            messages = {
                400: (
                    "Evaluator rejected the encrypted dataset. "
                    "Check its format and matching public files."
                ),
                413: "Encrypted dataset is too large.",
                415: "Evaluator requires application/json.",
                422: "Encrypted dataset validation failed.",
            }
            raise HTTPException(
                status_code=error.code,
                detail=messages[error.code],
            ) from error

        logger.warning(
            "HE upload evaluator returned HTTP %s",
            error.code,
        )
        raise HTTPException(
            status_code=502,
            detail="HE evaluator could not complete aggregation.",
        ) from error

    except (URLError, TimeoutError) as error:
        logger.warning("HE upload evaluator unavailable")
        raise HTTPException(
            status_code=503,
            detail="HE evaluator unavailable. Check Docker port 8001.",
        ) from error

    except (ValueError, KeyError, TypeError) as error:
        logger.warning("Invalid upload response from HE evaluator")
        raise HTTPException(
            status_code=502,
            detail="Invalid response from HE evaluator.",
        ) from error


@router.post("/aggregate-upload")
async def aggregate_upload(request: FastAPIRequest):
    content_type = request.headers.get(
        "content-type", ""
    ).split(";")[0].strip().lower()

    if content_type != "application/json":
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

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Encrypted dataset is empty.",
        )

    return await run_in_threadpool(
        forward_encrypted_dataset,
        bytes(body),
    )