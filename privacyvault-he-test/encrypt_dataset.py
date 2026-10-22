"""
Encrypt a fictional salary dataset using existing public files.

Does not generate keys or load a secret key.
Writes ciphertexts and metadata, not plaintext salaries.
"""

import base64
import hashlib
import json
import math
from getpass import getpass
from pathlib import Path

import numpy as np
from Pyfhel import Pyfhel


PUBLIC = Path("/public")
OUTPUT = Path("/output/encrypted-dataset.json")


def main():
    if OUTPUT.exists():
        raise SystemExit(
            "Output already exists. Rename or remove the previous "
            "encrypted-dataset.json before creating another dataset."
        )

    raw = getpass(
        "Enter fictional salaries separated by commas "
        "(input is hidden): "
    )

    try:
        salaries = [float(value.strip()) for value in raw.split(",")]
    except ValueError:
        raise SystemExit("Enter numbers separated by commas.")

    if not 1 <= len(salaries) <= 100:
        raise SystemExit("Enter between 1 and 100 salaries.")

    if any(
        not math.isfinite(salary)
        or salary < 0
        or salary > 1_000_000_000
        for salary in salaries
    ):
        raise SystemExit(
            "Each salary must be finite and between 0 "
            "and 1,000,000,000."
        )

    context_path = PUBLIC / "context.bin"
    public_key_path = PUBLIC / "public.key"

    encryptor = Pyfhel()
    encryptor.load_context(str(context_path))
    encryptor.load_public_key(str(public_key_path))

    ciphertexts = []

    for salary in salaries:
        encrypted = encryptor.encryptFrac(
            np.array([salary], dtype=np.float64)
        )
        ciphertexts.append(
            base64.b64encode(encrypted.to_bytes()).decode("ascii")
        )

    dataset = {
        "format_version": 1,
        "scheme": "CKKS",
        "operation": "sum",
        "employee_count": len(ciphertexts),
        "context_sha256": hashlib.sha256(
            context_path.read_bytes()
        ).hexdigest(),
        "public_key_sha256": hashlib.sha256(
            public_key_path.read_bytes()
        ).hexdigest(),
        "ciphertexts_base64": ciphertexts,
    }

    with OUTPUT.open("x", encoding="utf-8") as output:
        json.dump(dataset, output, indent=2)

    print(f"Encrypted records: {len(ciphertexts)}")
    print("Created /output/encrypted-dataset.json")
    print("No secret key was loaded.")
    print("No plaintext salaries were written to the output file.")


if __name__ == "__main__":
    main()