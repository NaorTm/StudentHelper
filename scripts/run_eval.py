# scripts/run_eval.py
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request


def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def run_question(base_url: str, question: str) -> tuple[dict, float]:
    conversation = http_post(f"{base_url}/chat/conversations", {})
    conversation_id = conversation["id"]

    start = time.time()
    answer = http_post(
        f"{base_url}/chat/conversations/{conversation_id}/messages",
        {"content": question},
    )
    elapsed = time.time() - start
    return answer, elapsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-html", required=True)
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    results = []
    latencies = []
    for item in data:
        answer, elapsed = run_question(args.base_url, item["question_text"])
        latencies.append(elapsed)
        results.append(
            {
                "question_id": item["question_id"],
                "question_text": item["question_text"],
                "answer": answer,
                "latency_seconds": elapsed,
                "evaluation_labels": {
                    "citation_precision": "manual_required",
                    "answer_correctness": "manual_required",
                    "abstention": "manual_required",
                },
            }
        )

    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0)

    report = {
        "model_config": {},
        "corpus_snapshot_id": None,
        "overall_metrics": {
            "latency_p50": p50,
            "latency_p95": p95,
            "citation_precision": "manual_required",
            "answer_correctness": "manual_required",
            "abstention_accuracy": "manual_required",
        },
        "per_question_results": results,
    }

    with open(args.output_json, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    html_lines = [
        "<html><head><title>Evaluation Report</title></head><body>",
        "<h1>Evaluation Report</h1>",
        f"<p>Latency p50: {p50:.3f}s, p95: {p95:.3f}s</p>",
        "<ul>",
    ]
    for item in results:
        html_lines.append("<li>")
        html_lines.append(f"<strong>{item['question_id']}</strong>: {item['question_text']}<br/>")
        html_lines.append(f"Confidence: {item['answer'].get('confidence')}<br/>")
        html_lines.append(f"Answer: {item['answer'].get('answer_text')}<br/>")
        html_lines.append("</li>")
    html_lines.append("</ul></body></html>")

    with open(args.output_html, "w", encoding="utf-8") as handle:
        handle.write("\n".join(html_lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
