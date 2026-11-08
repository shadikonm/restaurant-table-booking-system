"""Run an explicit local Ollama evaluation; never overwrite historical results."""

import argparse
import csv
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:3b")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output exists: select a new filename to preserve evidence")
    with args.data.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or not {"id", "text", "expected"}.issubset(rows[0]):
        parser.error("Input requires id,text,expected columns")
    labels = sorted({row["expected"] for row in rows})
    prompt = "Классифицируй сообщение. Верни только одну метку из списка: " + ", ".join(labels)
    results = []
    for row in rows:
        payload = {
            "model": args.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": row["text"]},
            ],
            "options": {"temperature": 0, "seed": 42},
        }
        request = Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        start = time.perf_counter()
        with urlopen(request, timeout=180) as response:
            answer = json.load(response)
        prediction = answer["message"]["content"].strip()
        results.append({
            "id": row["id"], "expected": row["expected"],
            "prediction": prediction, "correct": int(prediction == row["expected"]),
            "valid_label": int(prediction in labels),
            "seconds": round(time.perf_counter() - start, 4),
            "input_tokens": answer.get("prompt_eval_count"),
            "output_tokens": answer.get("eval_count"),
            "model": args.model, "prompt_version": "classification-v2",
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    args.out.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
    print(f"Saved {len(results)} real responses; accuracy={sum(r['correct'] for r in results)/len(results):.4f}")


if __name__ == "__main__":
    main()
