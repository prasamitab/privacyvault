"""
PrivacyVault: three-stage CKKS demonstration.

prepare:
    Creates keys and encrypts fictional salaries.

compute:
    Receives context and ciphertexts, but no secret key.
    Adds ciphertexts and saves the encrypted aggregate.

reveal:
    Loads the secret key and decrypts only the aggregate.

This is a local educational demonstration.
It does not protect against the Mac/Docker administrator.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
from Pyfhel import Pyfhel, PyCtxt


PRIVATE = Path("/private")
PUBLIC = Path("/public")
RESULTS = Path("/results")


def prepare():
    os.umask(0o077)

    secret_path = PRIVATE / "secret.key"

    if secret_path.exists():
        raise RuntimeError(
            "This demo folder already contains a secret key. "
            "Use a new demo folder instead of overwriting it."
        )

    key_holder = Pyfhel()
    key_holder.contextGen(
        scheme="CKKS",
        n=8192,
        scale=2**40,
        qi_sizes=[60, 40, 40, 60],
    )
    key_holder.keyGen()

    key_holder.save_context(str(PUBLIC / "context.bin"))
    key_holder.save_public_key(str(PUBLIC / "public.key"))
    key_holder.save_secret_key(str(secret_path))

    salaries = [50000.0, 70000.0]

    for index, salary in enumerate(salaries):
        ciphertext = key_holder.encryptFrac(
            np.array([salary], dtype=np.float64)
        )
        ciphertext.save(
            str(PUBLIC / f"salary_{index}.ctxt")
        )

    manifest = {
        "count": len(salaries),
        "scheme": "CKKS",
        "files": [
            f"salary_{index}.ctxt"
            for index in range(len(salaries))
        ],
    }

    (PUBLIC / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("PREPARE PASSED")
    print("Secret key saved in /private only.")
    print("Context and two ciphertexts saved in /public.")
    print("No plaintext salary files were saved.")


def compute():
    if PRIVATE.exists():
        raise RuntimeError(
            "The private directory must not be mounted "
            "in the computation container."
        )

    evaluator = Pyfhel()
    evaluator.load_context(str(PUBLIC / "context.bin"))

    manifest = json.loads(
        (PUBLIC / "manifest.json").read_text(encoding="utf-8")
    )

    ciphertexts = [
        PyCtxt(
            pyfhel=evaluator,
            fileName=str(PUBLIC / filename),
        )
        for filename in manifest["files"]
    ]

    if not ciphertexts:
        raise ValueError("No ciphertexts were provided")

    encrypted_total = ciphertexts[0]

    for ciphertext in ciphertexts[1:]:
        encrypted_total = encrypted_total + ciphertext

    # Negative test: this instance has never loaded a secret key.
    try:
        evaluator.decryptFrac(encrypted_total)
    except Exception as error:
        print(
            "Expected decryption failure without secret key:",
            type(error).__name__,
        )
    else:
        raise AssertionError(
            "Decryption unexpectedly succeeded without a secret key"
        )

    encrypted_total.save(str(RESULTS / "total.ctxt"))

    (RESULTS / "result.json").write_text(
        json.dumps(
            {
                "operation": "sum",
                "count": manifest["count"],
                "scheme": "CKKS",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("COMPUTE PASSED")
    print("Private key directory was not mounted.")
    print("Ciphertexts added using context only.")
    print("Encrypted aggregate saved in /results.")


def reveal():
    
    key_holder = Pyfhel()
    key_holder.load_context(str(PUBLIC / "context.bin"))
    key_holder.load_public_key(str(PUBLIC / "public.key"))
    key_holder.load_secret_key(str(PRIVATE / "secret.key"))

    encrypted_total = PyCtxt(
        pyfhel=key_holder,
        fileName=str(RESULTS / "total.ctxt"),
    )

    metadata = json.loads(
        (RESULTS / "result.json").read_text(encoding="utf-8")
    )

    total = float(
        key_holder.decryptFrac(encrypted_total)[0]
    )
    count = int(metadata["count"])
    average = total / count

    assert abs(total - 120000.0) < 0.1, total
    assert abs(average - 60000.0) < 0.1, average

    print(f"Aggregate total: INR {total:,.2f}")
    print(f"Public record count: {count}")
    print(f"Average from aggregate/count: INR {average:,.2f}")
    print("REVEAL PASSED")


def main():
    stages = {
        "prepare": prepare,
        "compute": compute,
        "reveal": reveal,
    }

    if len(sys.argv) != 2 or sys.argv[1] not in stages:
        raise SystemExit(
            "Usage: python separated_he.py "
            "[prepare|compute|reveal]"
        )

    stages[sys.argv[1]]()


if __name__ == "__main__":
    main()
