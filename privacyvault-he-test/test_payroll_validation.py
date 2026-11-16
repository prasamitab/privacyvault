"""Local evaluator tests. No secret key is required."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from he_service import evaluate_uploaded_dataset


INPUT = Path("/input/encrypted-dataset.json")
REPORT = Path("/output/evaluator-validation-tests.local.json")


def main():
    if REPORT.exists():
        raise SystemExit(
            "Report already exists. Choose a new report name "
            "before repeating this experiment."
        )

    original_bytes = INPUT.read_bytes()
    dataset = json.loads(original_bytes)
    tests = []

    try:
        result = evaluate_uploaded_dataset(copy.deepcopy(dataset))

        passed = (
            result.get("employee_count") == dataset["employee_count"]
            and result.get("scheme") == "CKKS"
            and result.get("operation") == "sum"
            and result.get("secret_key_loaded") is False
            and result.get("decryption_performed") is False
            and isinstance(result.get("encrypted_result_base64"), str)
            and bool(result["encrypted_result_base64"])
        )

        tests.append({
            "test": "Valid encrypted payroll dataset",
            "passed": passed,
            "observation": (
                "Encrypted result returned; numerical correctness "
                "requires the separate key-holder verifier."
            ),
        })
    except Exception as error:
        tests.append({
            "test": "Valid encrypted payroll dataset",
            "passed": False,
            "error_type": type(error).__name__,
        })

    cases = []

    wrong_context = copy.deepcopy(dataset)
    wrong_context["context_sha256"] = (
        "0" * 64
        if dataset["context_sha256"] != "0" * 64
        else "1" * 64
    )
    cases.append(("Wrong context identifier", wrong_context))

    wrong_count = copy.deepcopy(dataset)
    wrong_count["employee_count"] += 1
    cases.append(("Record count does not match ciphertexts", wrong_count))

    corrupt_ciphertext = copy.deepcopy(dataset)
    corrupt_ciphertext["ciphertexts_base64"][0] = "!!!invalid-base64!!!"
    cases.append(("Malformed ciphertext encoding", corrupt_ciphertext))

    wrong_key = copy.deepcopy(dataset)
    wrong_key["public_key_sha256"] = (
        "0" * 64
        if dataset["public_key_sha256"] != "0" * 64
        else "1" * 64
    )
    cases.append(("Wrong public-key identifier", wrong_key))

    for name, candidate in cases:
        try:
            evaluate_uploaded_dataset(candidate)
        except HTTPException as error:
            tests.append({
                "test": name,
                "passed": error.status_code == 400,
                "expected_status": 400,
                "actual_status": error.status_code,
                "detail": error.detail,
            })
        except Exception as error:
            tests.append({
                "test": name,
                "passed": False,
                "error_type": type(error).__name__,
                "observation": "Unexpected exception type.",
            })
        else:
            tests.append({
                "test": name,
                "passed": False,
                "observation": "Invalid input was unexpectedly accepted.",
            })

    unchanged = INPUT.read_bytes() == original_bytes
    passed_count = sum(item["passed"] for item in tests)

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Direct local evaluator-function tests, not HTTP tests.",
        "input_dataset_sha256": hashlib.sha256(
            original_bytes
        ).hexdigest(),
        "original_dataset_unchanged": unchanged,
        "tests_passed": passed_count,
        "tests_total": len(tests),
        "all_passed": passed_count == len(tests) and unchanged,
        "tests": tests,
        "limitations": [
            "Does not test authentication, CORS, or HTTP upload limits.",
            "Does not prove cryptographic security.",
            "Does not decrypt or check the aggregate numerically.",
        ],
    }

    with REPORT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    for item in tests:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"{status}: {item['test']}")

    print(f"Tests passed: {passed_count}/{len(tests)}")
    print(f"Original dataset unchanged: {unchanged}")

    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()