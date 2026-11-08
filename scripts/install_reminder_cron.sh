#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON_BIN:-$(command -v python3)}"
# This script prints a cron line for review; it does not change crontab automatically.
printf '*/15 * * * * cd "%s" && "%s" maintenance.py reminders >> "%s/logs/reminders.log" 2>&1\n' "$ROOT" "$PYTHON" "$ROOT"
echo 'Copy the line above into crontab -e after SMTP variables are available to cron.'
