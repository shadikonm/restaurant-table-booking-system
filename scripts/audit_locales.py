"""Audit Russian UI text dictionary and English/Kazakh mappings without changing pages."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/js/preferences.js"
REPORT = ROOT / "reports/locale_audit.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict", action="store_true", help="Fail on missing or blank translations"
    )
    args = parser.parse_args()
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"const dictionary = (\{.*?\});", source, re.S)
    if not match:
        raise SystemExit("Cannot locate locale dictionary")
    dictionary = json.loads(match.group(1))
    invalid = [
        key
        for key, value in dictionary.items()
        if not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(x, str) and x.strip() for x in value)
    ]
    report = {
        "entries": len(dictionary),
        "languages": ["ru", "kk", "en"],
        "missing_or_blank": invalid,
        "scope": "Dictionary completeness only; manual browser review still required",
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
