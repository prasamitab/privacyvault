#!/bin/bash
set -Eeuo pipefail

pids=()

cleanup() {
    trap - EXIT INT TERM
    if ((${#pids[@]})); then
        kill "${pids[@]}" 2>/dev/null || true
        wait "${pids[@]}" 2>/dev/null || true
    fi
}

trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

# Decode Render runtime public files
for filename in context.bin public.key; do
    encoded="/etc/secrets/${filename}.b64"
    if [ -r "$encoded" ]; then
        base64 --decode "$encoded" > "/public/$filename"
    fi
done

test -r /public/context.bin || {
    echo "Missing or unreadable /public/context.bin"
    exit 1
}

test -r /public/public.key || {
    echo "Missing or unreadable /public/public.key"
    exit 1
}

test ! -e /private || {
    echo "/private must not exist in this container"
    exit 1
}

/opt/he/bin/python -m uvicorn he_service:app \
    --app-dir /work/evaluator \
    --host 127.0.0.1 \
    --port 8001 \
    --workers 1 &
pids+=("$!")

/opt/backend/bin/python - <<'PY'
import time
import urllib.request

for _ in range(120):
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8001/health", timeout=2
        ) as response:
            if response.status == 200:
                break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Evaluator did not become ready")
PY

/opt/backend/bin/python -m uvicorn render_app:app \
    --app-dir /work/backend \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --workers 1 &
pids+=("$!")

set +e
wait -n "${pids[@]}"
status=$?
set -e

if [ "$status" -eq 0 ]; then
    status=1
fi
exit "$status"
