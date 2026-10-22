# PrivacyVault

A local educational prototype for privacy-preserving salary aggregation using CKKS homomorphic encryption.

PrivacyVault demonstrates how an evaluation service can add encrypted salary values without loading the secret key. A separate key-holder tool decrypts the aggregate and checks it against expected results.

> This is an educational prototype, not a production payroll platform. Use fictional data only.

## What the project demonstrates

- Local encryption using an existing public context and public key.
- Submission of an encrypted dataset through a React dashboard.
- A FastAPI bridge forwarding encrypted requests to a Docker evaluator.
- Real CKKS ciphertext addition using Pyfhel.
- Download of the encrypted aggregate and metadata.
- Separate key-holder decryption and functional verification.
- Rejection of malformed JSON, inconsistent record counts, and mismatched context identifiers.

## Architecture

    Local encryption tool
    Fictional salaries + public encryption files
                  |
                  v
    Encrypted dataset JSON
                  |
                  v
    React dashboard
                  |
                  v
    FastAPI bridge
                  |
                  v
    Docker CKKS evaluator
    Public context + ciphertexts; no secret key loaded
                  |
                  v
    Downloaded encrypted aggregate
                  |
                  v
    Separate key-holder verifier
    Matching context + keys
                  |
                  v
    Decrypted total + locally calculated average

The components run locally for this demonstration. Container separation does not protect against an administrator controlling the host machine.

## Technology stack

- React and Vite
- Tailwind CSS
- Axios
- FastAPI
- Python
- Pyfhel
- CKKS homomorphic encryption
- Docker

## Repository structure

    privacyvault-backend/
        app/
            routes/real_he.py    Bridge to the Docker evaluator

    privacyvault-frontend/
        src/RealHEDemo.jsx       Encrypted upload and result interface

    privacyvault-he-test/
        Dockerfile
        Dockerfile.service
        Dockerfile.single-process
        separated_he.py
        encrypt_dataset.py
        he_service.py
        verify_api_result.py
        verify_uploaded_result.py

The repository also contains earlier demonstration code. The real-HE workflow is separate from the mock employee-entry functionality.

## Main workflow

1. Prepare a local demonstration context and matching keys.
2. Encrypt fictional salaries using the local encryption script.
3. Select the generated encrypted-dataset.json in the dashboard.
4. Submit it for encrypted aggregation.
5. Download the encrypted aggregate.
6. Verify the downloaded result separately using the matching secret key.

The evaluator computes the encrypted sum.

The key holder calculates the average after decrypting the total:

    average = decrypted_total / public_record_count

The average is not a separate encrypted computation in this version.

## Local service addresses

| Component | Local address |
|---|---|
| Backend bridge | http://127.0.0.1:8000 |
| Docker evaluator | http://127.0.0.1:8001 |
| Frontend | Address printed by the Vite development server |

The current frontend and bridge use local service addresses. Hosted deployment requires configuration changes.

## Docker evaluator

Run the following commands from privacyvault-he-test.

The service Dockerfile depends on a locally available image named privacyvault-he-test. Build the base image first:

    docker build -f Dockerfile -t privacyvault-he-test .

Build the evaluator image:

    docker build -f Dockerfile.service -t privacyvault-he-service .

Create a fresh local dataset directory. Replace the example directory name if it already exists:

    export DEMO_DIR="$PWD/key-separation-local-demo"
    mkdir -p "$DEMO_DIR/public" "$DEMO_DIR/private" "$DEMO_DIR/results"

Prepare the original fictional two-record dataset:

    docker run --rm \
      --network none \
      --entrypoint python \
      --mount "type=bind,source=$PWD/separated_he.py,target=/separated_he.py,readonly" \
      --mount "type=bind,source=$DEMO_DIR/public,target=/public" \
      --mount "type=bind,source=$DEMO_DIR/private,target=/private" \
      privacyvault-he-service \
      /separated_he.py prepare

The prepare stage creates keys. Do not rerun it against an existing working key directory.

Start the evaluator with public files only:

    docker run --rm -d \
      --name privacyvault-he-service \
      -p 127.0.0.1:8001:8001 \
      --mount "type=bind,source=$DEMO_DIR/public,target=/public,readonly" \
      privacyvault-he-service

Check its health:

    curl http://127.0.0.1:8001/health

Do not mount the private-key directory into the evaluator.

## Encrypt a chosen dataset

From privacyvault-he-test:

    mkdir -p encrypted-exports

    docker run --rm -it \
      --network none \
      --entrypoint python \
      --mount "type=bind,source=$PWD/encrypt_dataset.py,target=/encrypt_dataset.py,readonly" \
      --mount "type=bind,source=$DEMO_DIR/public,target=/public,readonly" \
      --mount "type=bind,source=$PWD/encrypted-exports,target=/output" \
      privacyvault-he-service \
      /encrypt_dataset.py

Enter fictional salaries when prompted. Input is hidden.

Example:

    45000,55000,70000

The script writes:

    encrypted-exports/encrypted-dataset.json

It does not load a secret key or write plaintext salaries to the export.

The script refuses to overwrite an existing export. Preserve or rename the previous output before generating another.

## API routes

### Backend bridge

- POST /api/v1/real-he/aggregate-demo
- POST /api/v1/real-he/aggregate-upload

### Docker evaluator

- GET /health
- POST /aggregate
- POST /aggregate-upload

The upload routes accept a JSON dataset, not a multipart file upload.

Current configured limits include:

- 1–100 records.
- 64 MiB request body.
- 1 MiB decoded size per submitted ciphertext.

Request-size limits may prevent some otherwise valid record collections from fitting within the overall upload limit.

## Verify the browser download

Start the frontend and backend using the development configuration for each component.

In the dashboard:

1. Select encrypted-dataset.json.
2. Click "Aggregate uploaded dataset".
3. Download privacyvault-uploaded-result.json.

From privacyvault-he-test, with DEMO_DIR set to the matching key directory:

    docker run --rm \
      --network none \
      --entrypoint python \
      --mount "type=bind,source=$PWD/verify_uploaded_result.py,target=/verify_uploaded_result.py,readonly" \
      --mount "type=bind,source=$HOME/Downloads/privacyvault-uploaded-result.json,target=/response.json,readonly" \
      --mount "type=bind,source=$DEMO_DIR/public/context.bin,target=/keys/context.bin,readonly" \
      --mount "type=bind,source=$DEMO_DIR/public/public.key,target=/keys/public.key,readonly" \
      --mount "type=bind,source=$DEMO_DIR/private/secret.key,target=/keys/secret.key,readonly" \
      privacyvault-he-service \
      /verify_uploaded_result.py

The current uploaded-result verifier expects the three-record example:

    Aggregate total: INR 170,000.00
    Public record count: 3
    Average from aggregate/count: INR 56,666.67
    PASS: encrypted API response verified by key holder.

These expected values are specific to that test dataset. Update the local verification expectations before testing different inputs.

CKKS uses approximate arithmetic, so verification allows a small numerical tolerance.

## Verified tests

| Test | Observed outcome |
|---|---|
| Fixed two-record aggregate | Total near INR 120,000; verification passed |
| Uploaded three-record aggregate | Total near INR 170,000; verification passed |
| Browser-downloaded uploaded result | Key-holder verification passed |
| Malformed JSON | HTTP 400 |
| Incorrect record count | HTTP 400 |
| Mismatched context identifier | HTTP 400 |

Corrupted-ciphertext, oversized-request, evaluator-unavailable, and clean-machine setup tests still require documented results.

## Security boundaries and limitations

- No production authentication or aggregate-release policy.
- Use fictional data only.
- All submitted ciphertexts must use a compatible context and key setup.
- Fingerprints identify configured public files; they are not authentication or proof of honest input generation.
- Record count, ciphertext sizes, and processing time are visible metadata.
- The key holder can decrypt compatible individual ciphertexts if given them; the secret key is not restricted to aggregate-only decryption.
- Small or overlapping released aggregates can disclose individual values.
- Known-answer verification is a functional test, not a cryptographic proof of correct server evaluation.
- The mock employee form is separate from the real CKKS upload workflow.
- The application has not been established as production-ready or independently security-audited.

## Repository hygiene

Do not commit:

- Secret keys or generated key directories.
- Credentials or sensitive .env files.
- Real salary records or personal databases.
- Local generated exports and result files.
- Virtual environments or node_modules.

Generate a fresh local demonstration setup rather than distributing a private key.

## Future work

- Reusable command-line verification options.
- Automated regression and failure tests.
- Complete clean-machine startup instructions.
- Configurable deployment addresses.
- Authentication, request controls, and aggregate-release policy.
- Restricted HTTPS demonstration deployment.

## Project contribution

PrivacyVault does not introduce a new encryption algorithm.

Its contribution is an integrated educational workflow combining real CKKS aggregation, separated evaluation and decryption roles, encrypted dataset submission, downloadable results, and independent key-holder verification.
