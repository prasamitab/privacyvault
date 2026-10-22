"""
PrivacyVault mock computation module.

WARNING:
- This is NOT genuine encryption or homomorphic encryption.
- Base64 encoding does not protect salary confidentiality.
- Computations decode individual values before calculating results.
- Use fictional data only.

The method names are retained for compatibility with the existing API.
"""

import base64
import hashlib
import math
import time
from typing import List, Tuple


class MockHomomorphicEncryption:
    def __init__(self):
        self.context_info = {
            "scheme": "Base64 simulation (NOT CKKS)",
            "poly_modulus_degree": 4096,
            "scale": 2**40,
            "simulation": True,
            "note": (
                "No cryptographic confidentiality. "
                "Polynomial degree and scale are illustrative only."
            ),
        }

    @staticmethod
    def _validate_number(value: float) -> float:
        number = float(value)

        if not math.isfinite(number):
            raise ValueError("Value must be a finite number")

        return number

    def encrypt_salary(self, salary: float) -> Tuple[str, dict]:
        """Encode a value using the existing mock record format."""
        started = time.perf_counter()

        salary = self._validate_number(salary)
        salary_text = str(salary)

        checksum = hashlib.sha256(
            salary_text.encode("utf-8")
        ).hexdigest()[:32]

        payload = f"ENC_{salary_text}_{checksum}"

        encoded_value = base64.b64encode(
            payload.encode("utf-8")
        ).decode("ascii")

        elapsed_ms = (time.perf_counter() - started) * 1000

        return encoded_value, {
            "encryption_time_ms": elapsed_ms,
            "context": self.context_info.copy(),
            "simulation": True,
        }

    def decrypt_salary(self, encrypted_hex: str) -> Tuple[float, dict]:
        """
        Decode an existing mock value.

        The parameter name is retained for API compatibility.
        Its contents are Base64, not hexadecimal ciphertext.
        """
        started = time.perf_counter()

        if not isinstance(encrypted_hex, str):
            raise ValueError("Mock encoded value must be a string")

        try:
            payload = base64.b64decode(
                encrypted_hex.encode("ascii"),
                validate=True,
            ).decode("utf-8")

            parts = payload.split("_", 2)

            if len(parts) != 3 or parts[0] != "ENC":
                raise ValueError("Invalid mock record format")

            salary_text = parts[1]
            stored_checksum = parts[2]

            expected_checksum = hashlib.sha256(
                salary_text.encode("utf-8")
            ).hexdigest()[:32]

            if stored_checksum != expected_checksum:
                raise ValueError("Mock record checksum mismatch")

            salary = self._validate_number(salary_text)

        except (ValueError, UnicodeError) as exc:
            raise ValueError(
                "Could not decode the mock salary record"
            ) from exc

        elapsed_ms = (time.perf_counter() - started) * 1000

        return salary, {
            "decryption_time_ms": elapsed_ms,
            "simulation": True,
        }

    def add_encrypted(
        self,
        encrypted_hex1: str,
        encrypted_hex2: str,
    ) -> Tuple[str, dict]:
        """Mock addition: decode, add, then encode."""
        return self.compute_sum_encrypted(
            [encrypted_hex1, encrypted_hex2]
        )

    def compute_sum_encrypted(
        self,
        encrypted_salaries: List[str],
    ) -> Tuple[str, dict]:
        """Mock sum: individual values are decoded internally."""
        if not encrypted_salaries:
            raise ValueError("No salary records provided")

        started = time.perf_counter()

        salaries = [
            self.decrypt_salary(record)[0]
            for record in encrypted_salaries
        ]

        total = math.fsum(salaries)
        encoded_total, _ = self.encrypt_salary(total)

        elapsed_ms = (time.perf_counter() - started) * 1000

        return encoded_total, {
            "computation_time_ms": elapsed_ms,
            "operation": "sum",
            "employee_count": len(encrypted_salaries),
            "simulation": True,
        }

    def compute_average_encrypted(
        self,
        encrypted_salaries: List[str],
    ) -> Tuple[str, dict]:
        """Mock average, returning a string and a metadata dictionary."""
        if not encrypted_salaries:
            raise ValueError("No salary records provided")

        started = time.perf_counter()

        encoded_total, _ = self.compute_sum_encrypted(
            encrypted_salaries
        )
        total, _ = self.decrypt_salary(encoded_total)

        average = total / len(encrypted_salaries)

        # Unpack first: do not return a nested tuple.
        encoded_average, _ = self.encrypt_salary(average)

        elapsed_ms = (time.perf_counter() - started) * 1000

        return encoded_average, {
            "computation_time_ms": elapsed_ms,
            "operation": "average",
            "employee_count": len(encrypted_salaries),
            "simulation": True,
        }

    def compute_weighted_average_encrypted(
        self,
        encrypted_salaries: List[str],
        weights: List[float],
    ) -> Tuple[str, dict]:
        """Mock weighted average using public, nonnegative weights."""
        if not encrypted_salaries:
            raise ValueError("No salary records provided")

        if len(encrypted_salaries) != len(weights):
            raise ValueError(
                "Each salary record must have a matching weight"
            )

        started = time.perf_counter()

        checked_weights = [
            self._validate_number(weight)
            for weight in weights
        ]

        if any(weight < 0 for weight in checked_weights):
            raise ValueError("Weights cannot be negative")

        total_weight = math.fsum(checked_weights)

        if total_weight <= 0:
            raise ValueError("Sum of weights must be greater than zero")

        salaries = [
            self.decrypt_salary(record)[0]
            for record in encrypted_salaries
        ]

        weighted_average = math.fsum(
            salary * (weight / total_weight)
            for salary, weight in zip(salaries, checked_weights)
        )

        encoded_average, _ = self.encrypt_salary(weighted_average)

        elapsed_ms = (time.perf_counter() - started) * 1000

        return encoded_average, {
            "computation_time_ms": elapsed_ms,
            "operation": "weighted_average",
            "employee_count": len(encrypted_salaries),
            "total_weight": total_weight,
            "simulation": True,
        }

    def get_performance_metrics(self, num_samples: int = 10) -> dict:
        """
        Measure this mock's runtime.

        Compatibility field names are retained, but these numbers
        are NOT homomorphic-encryption benchmarks.
        """
        if not isinstance(num_samples, int) or num_samples < 1:
            raise ValueError("num_samples must be a positive integer")

        test_salaries = [50000.0, 70000.0, 90000.0]

        encryption_times = []
        decryption_times = []
        computation_times = []
        plaintext_times = []

        for _ in range(num_samples):
            encoded_records = []

            for salary in test_salaries:
                encoded, metadata = self.encrypt_salary(salary)
                encoded_records.append(encoded)
                encryption_times.append(
                    metadata["encryption_time_ms"]
                )

                _, metadata = self.decrypt_salary(encoded)
                decryption_times.append(
                    metadata["decryption_time_ms"]
                )

            _, metadata = self.compute_sum_encrypted(
                encoded_records
            )
            computation_times.append(
                metadata["computation_time_ms"]
            )

            started = time.perf_counter()
            math.fsum(test_salaries)
            plaintext_times.append(
                (time.perf_counter() - started) * 1000
            )

        average_encryption = math.fsum(encryption_times) / len(
            encryption_times
        )
        average_decryption = math.fsum(decryption_times) / len(
            decryption_times
        )
        average_computation = math.fsum(computation_times) / num_samples
        average_plaintext = math.fsum(plaintext_times) / num_samples

        overhead_ratio = (
            average_computation / average_plaintext
            if average_plaintext > 0
            else 0.0
        )

        return {
            "avg_encryption_time_ms": average_encryption,
            "avg_decryption_time_ms": average_decryption,
            "encrypted_computation_time_ms": average_computation,
            "plaintext_computation_time_ms": average_plaintext,
            "overhead_ratio": overhead_ratio,
            "encryption_scheme": self.context_info["scheme"],
            "poly_modulus_degree": 4096,
            "simulation": True,
            "note": (
                "Measured Base64 mock timings only; "
                "not real encryption or HE performance."
            ),
        }


# Keep this outside the class, with no indentation.
he_instance = MockHomomorphicEncryption()