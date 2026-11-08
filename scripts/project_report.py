"""Reproducible repository metrics; optional local Ollama narrative.

python scripts/project_report.py --snapshot evidence/github_issues.json --out reports/project
python scripts/project_report.py --live --ollama qwen2.5:3b
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

REPO = "shadikonm/restaurant-table-booking-system"
PROMPT = (
    "Составь короткий статус PM только по JSON. Не придумывай сроки, расходы, "
    "причины и решения. Закрытие Issue не означает завершение спринта. "
    "Разделы: результаты, ограничения, риски, следующие действия. "
    "Числа переноси без изменений. Не объявляй CI развёртыванием.\n"
)


def fetch_issues():
    result = []
    for page in range(1, 101):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "TABLE-report",
        }
        if os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
        request = Request(
            f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}",
            headers=headers,
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        result.extend(x for x in batch if "pull_request" not in x)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("Pagination limit reached; export is incomplete")
    return result


def summarize(issues):
    periods = []
    for start, end in [("2026-09-27", "2026-10-03"), ("2026-10-04", "2026-10-10")]:
        closed = [
            x
            for x in issues
            if x.get("closed_at") and start <= x["closed_at"][:10] <= end
        ]
        periods.append(
            {
                "start": start,
                "end": end,
                "closed": len(closed),
                "issue_numbers": sorted(x["number"] for x in closed),
                "cycle_time": None,
                "p85_cycle_time": None,
            }
        )
    return {
        "total": len(issues),
        "open": sum(x["state"] == "open" for x in issues),
        "closed": sum(x["state"] == "closed" for x in issues),
        "periods": periods,
        "limitation": "Closure events are measured; historical In Progress and Review transitions are unavailable. Lead time since creation is not cycle time.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("reports/project"))
    parser.add_argument("--ollama", help="Explicit opt-in; local Ollama model name")
    args = parser.parse_args()
    if not args.live and not args.snapshot:
        parser.error("Choose --live or --snapshot FILE")
    issues = fetch_issues() if args.live else json.loads(args.snapshot.read_text())
    summary = summarize(issues)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "issues.json").write_text(
        json.dumps(issues, ensure_ascii=False, indent=2)
    )
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )
    lines = [
        "# TABLE Отчёт PM",
        "",
        "Дата формирования: " + datetime.now(timezone.utc).isoformat(),
        f"Всего Issues: {summary['total']}; закрыто: {summary['closed']}; открыто: {summary['open']}.",
        "",
    ]
    for period in summary["periods"]:
        lines.append(
            f"Период {period['start']} — {period['end']}: закрыто {period['closed']}; номера {period['issue_numbers']}."
        )
    lines += [
        "",
        summary["limitation"],
        "",
        "DORA: Н/Д — нет подтверждённого журнала развёртываний.",
        "Фактические расходы: Н/Д — нужен журнал платежей и трудозатрат.",
    ]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    with (args.out / "periods.csv").open("w", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "start",
                "end",
                "closed",
                "issue_numbers",
                "cycle_time",
                "p85_cycle_time",
            ],
        )
        writer.writeheader()
        writer.writerows(summary["periods"])
    if args.ollama:
        body = json.dumps(
            {
                "model": args.ollama,
                "prompt": PROMPT + json.dumps(summary, ensure_ascii=False),
                "stream": False,
                "options": {"temperature": 0},
            }
        ).encode()
        with urlopen(
            Request(
                "http://127.0.0.1:11434/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            ),
            timeout=180,
        ) as response:
            result = json.load(response)
        (args.out / "model_response.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2)
        )
        (args.out / "model_report.md").write_text(result["response"], encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
