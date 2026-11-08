#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${LOAD_HOST:-http://127.0.0.1:5000}"
if [[ "$HOST" != 'http://127.0.0.1:5000' && "$HOST" != 'http://localhost:5000' ]]; then
  echo 'Safety: load testing is restricted to your local Flask server.' >&2
  exit 2
fi
mkdir -p reports
locust -f locustfile.py --headless -u "${LOAD_USERS:-5}" -r "${LOAD_SPAWN_RATE:-1}" -t "${LOAD_DURATION:-30s}" --host "$HOST" --csv reports/locust --html reports/locust.html --only-summary
