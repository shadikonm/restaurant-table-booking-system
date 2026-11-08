#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
python3 -m compileall -q app.py assistant_service.py maintenance.py monitor.py tests scripts
find static/js -name '*.js' -print0 | xargs -0 -n1 node --check
python3 scripts/audit_locales.py --strict
python3 -m unittest discover -s tests -v 2>&1 | tee reports/unit_tests.txt
