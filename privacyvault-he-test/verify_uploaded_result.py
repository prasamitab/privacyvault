"""
Verify the encrypted aggregate returned by the HE API.

Runs on the key-holder side only.
Decrypts the aggregate, not individual salary ciphertexts.
"""

import base64
import json
import math
import tempfile
from pathlib import Path

from Pyfhel import Pyfhel, PyCtxt


def main():
    response = json.loads(
        Path("/response.json").read_text(encoding="utf-8")
    )

    if response.get("scheme") != "CKKS":
        raise ValueError("Expected a CKKS response")

    if response.get("operation") != "sum":
        raise ValueError("Expected an encrypted sum")

    count = response.get("employee_count")

    if type(count) is not int or count <= 0:
        raise ValueError("Invalid record count")

    ciphertext_bytes = base64.b64decode(
        response["encrypted_result_base64"],
        validate=True,
    )

    if len(ciphertext_bytes) != response["ciphertext_size_bytes"]:
        raise ValueError("Ciphertext size does not match the response")

    key_holder = Pyfhel()
    key_holder.load_context("/keys/context.bin")
    key_holder.load_public_key("/keys/public.key")
    key_holder.load_secret_key("/keys/secret.key")

    with tempfile.TemporaryDirectory() as directory:
        ciphertext_path = Path(directory) / "api_total.ctxt"
        ciphertext_path.write_bytes(ciphertext_bytes)

        encrypted_total = PyCtxt(
            pyfhel=key_holder,
            fileName=str(ciphertext_path),
        )

        total = float(
            key_holder.decryptFrac(encrypted_total)[0]
        )

    average = total / count

    if not math.isfinite(total):
        raise AssertionError("Decrypted total is not finite")

        # Expected values for the fictional upload test:
    # 45000, 55000, 70000
    expected_count = 3
    expected_total = 170000.0
    expected_average = expected_total / expected_count

    if count != expected_count:
        raise AssertionError(f"Unexpected count: {count}")

    if abs(total - expected_total) >= 0.1:
        raise AssertionError(f"Unexpected total: {total}")

    if abs(average - expected_average) >= 0.1:
        raise AssertionError(f"Unexpected average: {average}")

    print("API ciphertext loaded successfully.")
    print(f"Aggregate total: INR {total:,.2f}")
    print(f"Public record count: {count}")
    print(f"Average from aggregate/count: INR {average:,.2f}")
    print("PASS: encrypted API response verified by key holder.")


if __name__ == "__main__":
    main()
