"""Read-only local benchmark using a synthetic database and 200 concurrent users."""

import json
import logging
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier, Thread
from urllib.request import urlopen
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from werkzeug.serving import ThreadedWSGIServer

logging.getLogger("werkzeug").setLevel(logging.ERROR)
app.app.logger.setLevel(logging.ERROR)
with tempfile.TemporaryDirectory() as tmp:
    app.DATABASE = str(Path(tmp) / "load.db")
    app.init_db()

    class BenchmarkServer(ThreadedWSGIServer):
        request_queue_size = 512

    server = BenchmarkServer("127.0.0.1", 0, app.app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_port}"
    date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    urls = [
        "/api/menu",
        "/health",
        f"/api/availability?date={date}&time=18:00&guests=2",
    ]
    barrier = Barrier(200)

    def user(_):
        barrier.wait(timeout=30)
        values = []
        for url in urls:
            start = time.perf_counter()
            try:
                with urlopen(root + url, timeout=30) as response:
                    response.read()
                    ok = response.status == 200
            except Exception:
                ok = False
            values.append(((time.perf_counter() - start) * 1000, ok))
        return values

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=200) as pool:
        rows = [x for result in pool.map(user, range(200)) for x in result]
    duration = time.perf_counter() - start
    times = sorted(x[0] for x in rows)
    result = {
        "users": 200,
        "requests": len(rows),
        "errors": sum(not x[1] for x in rows),
        "duration_seconds": duration,
        "rps": len(rows) / duration,
        "p50_ms": times[int(0.5 * len(times)) - 1],
        "p95_ms": times[int(0.95 * len(times)) - 1],
        "scope": "600 read-only local requests, synthetic DB, Werkzeug threaded server; excludes browser rendering and writes",
    }
    print(json.dumps(result, indent=2))
    out = Path(__file__).resolve().parents[1] / "reports/load_200.json"
    out.write_text(json.dumps(result, indent=2))
    server.shutdown()
