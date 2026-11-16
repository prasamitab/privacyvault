# PrivacyVault: Confidential Payroll Analytics

## Purpose

Demonstrate outsourced payroll aggregation on encrypted numeric
values while keeping the matching secret key on the data owner's
machine.

## Demonstration dataset

- Source: NYC Open Data, Citywide Payroll Data (Fiscal Year)
- Dataset identifier: k397-673e
- Fiscal year: 2025
- Agency: DEPT OF ED PEDAGOGICAL
- Selected records: 25
- Metric: regular_gross_paid
- Currency: USD
- Employee names were not requested.

The importer selected the latest fiscal year with eligible
named-agency records, then the agency with the most eligible
records, then the first 25 eligible rows ordered by source row ID.

Eligibility required positive regular pay, nonnegative overtime,
and values within the prototype's supported input range.

This is a non-random sample, not an agency-wide payroll total.
The source data is public, not confidential.

## Workflow

1. Download the documented sample locally.
2. Calculate a local reference.
3. Encrypt regular-pay values using existing public files.
4. Upload ciphertexts to the hosted evaluator.
5. Download the encrypted sum.
6. Decrypt locally using the matching secret key.
7. Compare against the local reference.

The mean is calculated locally from the decrypted sum and
public record count.

## Recorded hosted experiment

- Record count: 25
- Expected total: USD 2,794,837.11
- Expected mean per selected record: USD 111,793.4844
- Total absolute error: approximately 4.2e-9 USD
- Selected absolute tolerance: USD 0.01
- Local encryption time: approximately 142.39 ms
- Browser-observed request duration: approximately 20.23 seconds
- Client-recorded API: https://privacyvault.onrender.com
- Numerical verification: PASS

These are measurements from one run, not general performance
guarantees. The request duration is not the evaluator-only
computation time.

## Local evaluator validation tests

1. Valid encrypted dataset: accepted.
2. Wrong context identifier: rejected.
3. Inconsistent record count: rejected.
4. Malformed ciphertext encoding: rejected.
5. Wrong public-key identifier: rejected.

Result: 5/5 tests passed.
Original encrypted dataset remained unchanged.

These are direct local evaluator-function tests, not HTTP,
authentication, or CORS tests.

## Trust model and limitations

- The cloud computation service should not receive the secret key.
- The data owner already knows the original payroll values.
- The key holder could decrypt individual ciphertexts if given them;
  this prototype does not enforce aggregate-only decryption.
- Numerical verification is not a cryptographic proof of server
  execution or result authenticity.
- Public-file hashes identify expected files; they do not establish
  the truth or provenance of the payroll values.
- Public source data demonstrates the workflow, not source secrecy.
- This is not a production payroll system or a multi-party protocol.
- The current upload format supports at most 100 records.

## Local evidence

The local-experiments directory contains the source metadata,
sample CSV, encrypted dataset, downloaded result, numerical
verification report, and evaluator-test report.

Keep local references and decrypted reports out of ordinary
application uploads. Never commit secret keys or credentials.