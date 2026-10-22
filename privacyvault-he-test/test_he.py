"""
Standalone PrivacyVault CKKS smoke test.

This demonstrates real ciphertext addition.
It is not yet integrated with the web application.

Both roles run in one process for this first test.
Actual process/key separation is a later milestone.
"""

from importlib.metadata import version

import numpy as np
from Pyfhel import Pyfhel


def main():
    print("Pyfhel version:", version("Pyfhel"))

    key_holder = Pyfhel()
    key_holder.contextGen(
        scheme="CKKS",
        n=8192,
        scale=2**40,
        qi_sizes=[60, 40, 40, 60],
    )
    key_holder.keyGen()

    salary_a = np.array([50000.0], dtype=np.float64)
    salary_b = np.array([70000.0], dtype=np.float64)

    encrypted_a = key_holder.encryptFrac(salary_a)
    encrypted_b = key_holder.encryptFrac(salary_b)

    print("Two fictional salaries encrypted.")
    print("Ciphertext A size:", len(encrypted_a.to_bytes()), "bytes")
    print("Ciphertext B size:", len(encrypted_b.to_bytes()), "bytes")

    # Evaluation stage: no decryption is called here.
    encrypted_total = encrypted_a + encrypted_b

    print("Ciphertext addition completed without decrypting inputs.")

    # Key-holder stage: decrypt only the aggregate.
    total = float(key_holder.decryptFrac(encrypted_total)[0])

    public_count = 2
    average = total / public_count

    assert abs(total - 120000.0) < 0.1, (
        f"Unexpected total: {total}"
    )
    assert abs(average - 60000.0) < 0.1, (
        f"Unexpected average: {average}"
    )

    print(f"Decrypted aggregate total: INR {total:,.2f}")
    print(f"Average from aggregate/public count: INR {average:,.2f}")
    print("PASS: real CKKS ciphertext addition verified.")


if __name__ == "__main__":
    main()
