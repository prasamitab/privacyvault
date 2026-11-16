"""Verify an encrypted aggregate against a trusted local reference."""

import argparse
import base64
import hashlib
import json
import math
from pathlib import Path

from Pyfhel import Pyfhel, PyCtxt


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--public", type=Path, default=Path("/public"))
    parser.add_argument("--secret", type=Path, default=Path("/secret.key"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=0.01)
    args = parser.parse_args()

    require(
        math.isfinite(args.tolerance) and args.tolerance > 0,
        "Tolerance must be positive and finite.",
    )
    require(not args.report.exists(), "Report already exists.")

    result = json.loads(args.result.read_text(encoding="utf-8"))
    reference = json.loads(args.reference.read_text(encoding="utf-8"))

    require(
        digest(args.dataset) == reference["encrypted_dataset_sha256"],
        "Encrypted dataset differs from the local reference.",
    )

    for field, filename in (
        ("context_sha256", "context.bin"),
        ("public_key_sha256", "public.key"),
    ):
        expected = digest(args.public / filename)
        require(reference.get(field) == expected,
                f"Local reference mismatch: {field}")
        require(result.get(field) == expected,
                f"API result mismatch: {field}")

    require(result.get("scheme") == "CKKS", "Expected CKKS.")
    require(result.get("operation") == "sum", "Expected sum.")

    count = result.get("employee_count")
    require(type(count) is int and count > 0, "Invalid result count.")
    require(count == reference["record_count"], "Record count mismatch.")

    data = base64.b64decode(
        result["encrypted_result_base64"], validate=True
    )
    require(
        len(data) == result["ciphertext_size_bytes"],
        "Ciphertext size mismatch.",
    )

    holder = Pyfhel()
    holder.load_context(str(args.public / "context.bin"))
    holder.load_public_key(str(args.public / "public.key"))
    holder.load_secret_key(str(args.secret))

    encrypted = PyCtxt(pyfhel=holder, bytestring=data)
    total = float(holder.decryptFrac(encrypted)[0])
    require(math.isfinite(total), "Decrypted total is not finite.")

    average = total / count
    expected_total = float(reference["expected_total"])
    expected_average = float(reference["expected_average"])
    require(
        math.isfinite(expected_total) and math.isfinite(expected_average),
        "Invalid reference values.",
    )

    total_error = abs(total - expected_total)
    average_error = abs(average - expected_average)
    passed = (
        total_error <= args.tolerance
        and average_error <= args.tolerance
    )

    report = {
        "passed": passed,
        "source": reference["source"],
        "currency": reference["currency"],
        "period": reference["period"],
        "record_count": count,
        "expected_total": expected_total,
        "decrypted_total": total,
        "total_absolute_error": total_error,
        "expected_average": expected_average,
        "decrypted_average": average,
        "average_absolute_error": average_error,
        "absolute_tolerance": args.tolerance,
        "encryption_time_ms": reference["encryption_time_ms"],
        "server_computation_time_ms": result.get("computation_time_ms"),
        "encrypted_dataset_bytes": args.dataset.stat().st_size,
        "result_file_sha256": digest(args.result),
        "note": (
            "Local numerical consistency test, not a cryptographic "
            "proof of server execution or result authenticity."
        ),
    }

    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    currency = reference["currency"]
    print(f"Record count: {count}")
    print(f"Decrypted total: {currency} {total:,.6f}")
    print(f"Decrypted mean: {currency} {average:,.6f}")
    print(f"Total absolute error: {total_error:.10f}")
    print(f"Mean absolute error: {average_error:.10f}")
    print(f"Absolute tolerance: {args.tolerance}")
    print("PASS" if passed else "FAIL")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()