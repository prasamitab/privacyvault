"""Encrypt a salary CSV using existing public files only."""

import argparse
import base64
import csv
import hashlib
import json
import math
import os
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
from Pyfhel import Pyfhel


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--column", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--public", type=Path, default=Path("/public"))
    parser.add_argument("--output-dir", type=Path, default=Path("/output"))
    args = parser.parse_args()

    os.umask(0o077)
    encrypted_path = args.output_dir / "encrypted-dataset.json"
    reference_path = args.output_dir / "reference.local.json"

    if encrypted_path.exists() or reference_path.exists():
        raise SystemExit(
            "Output already exists. Use a new experiment folder."
        )

    values = []

    with args.csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)

        if args.column not in (reader.fieldnames or []):
            raise SystemExit(f"Missing CSV column: {args.column}")

        for row_number, row in enumerate(reader, start=2):
            try:
                value = Decimal(row[args.column].strip())
            except (InvalidOperation, AttributeError):
                raise SystemExit(
                    f"Invalid salary at CSV row {row_number}"
                )

            if (
                not value.is_finite()
                or value < 0
                or value > Decimal("1000000000")
            ):
                raise SystemExit(
                    f"Out-of-range salary at CSV row {row_number}"
                )

            values.append(value)

            if len(values) > 100:
                raise SystemExit("Maximum supported dataset size is 100.")

    if not values:
        raise SystemExit("CSV contains no salary records.")

    context = args.public / "context.bin"
    public_key = args.public / "public.key"
    context_hash = sha256(context)
    key_hash = sha256(public_key)

    encryptor = Pyfhel()
    encryptor.load_context(str(context))
    encryptor.load_public_key(str(public_key))

    started = time.perf_counter()
    ciphertexts = []

    for value in values:
        number = float(value)

        if not math.isfinite(number):
            raise SystemExit("Salary cannot be represented as a float.")

        ciphertext = encryptor.encryptFrac(
            np.array([number], dtype=np.float64)
        )
        ciphertexts.append(
            base64.b64encode(ciphertext.to_bytes()).decode("ascii")
        )

    encryption_ms = (time.perf_counter() - started) * 1000

    dataset = {
        "format_version": 1,
        "scheme": "CKKS",
        "operation": "sum",
        "employee_count": len(values),
        "context_sha256": context_hash,
        "public_key_sha256": key_hash,
        "ciphertexts_base64": ciphertexts,
    }

    total = sum(values, Decimal("0"))
    reference = {
        "source": args.source,
        "currency": args.currency,
        "period": args.period,
        "salary_column": args.column,
        "input_csv_sha256": sha256(args.csv),
        "record_count": len(values),
        "expected_total": str(total),
        "expected_average": str(total / Decimal(len(values))),
        "context_sha256": context_hash,
        "public_key_sha256": key_hash,
        "encryption_time_ms": encryption_ms,
        "note": "Local reference only. Do not upload to the evaluator.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with encrypted_path.open("x", encoding="utf-8") as handle:
        json.dump(dataset, handle)

    reference["encrypted_dataset_sha256"] = sha256(encrypted_path)
    reference["encrypted_dataset_bytes"] = encrypted_path.stat().st_size

    with reference_path.open("x", encoding="utf-8") as handle:
        json.dump(reference, handle, indent=2)

    print(f"Encrypted records: {len(values)}")
    print(f"Encryption time: {encryption_ms:.2f} ms")
    print(f"Upload size: {encrypted_path.stat().st_size:,} bytes")
    print("Upload file: encrypted-dataset.json")
    print("Keep local: reference.local.json")
    print("No secret key was loaded.")


if __name__ == "__main__":
    main()