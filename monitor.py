"""Simple uptime probe: python monitor.py; scheduler can run every 5 minutes."""

import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

url = os.environ.get("HEALTH_URL", "http://127.0.0.1:5000/health")
try:
    with urlopen(url, timeout=5) as response:
        body = response.read().decode("utf-8")
        healthy = response.status == 200 and '"ok"' in body
except Exception as exc:
    healthy = False
    body = type(exc).__name__
status = "OK" if healthy else "FAIL"
line = f"{datetime.now().isoformat(timespec='seconds')} {status} {url} {body[:180]}\n"
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(exist_ok=True)
with (log_dir / "uptime.log").open("a", encoding="utf-8") as output:
    output.write(line)
print(line.strip())
sys.exit(0 if healthy else 1)
