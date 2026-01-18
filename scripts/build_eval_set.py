# scripts/build_eval_set.py
from __future__ import annotations

import argparse
import json
import sys


REQUIRED_FIELDS = {
    "question_id",
    "question_text",
    "intent_category",
    "ground_truth_citations",
    "ground_truth_answer_summary",
}


def validate_item(item: dict, index: int) -> list[str]:
    errors = []
    missing = REQUIRED_FIELDS - set(item.keys())
    if missing:
        errors.append(f"item {index} missing fields: {sorted(missing)}")
    if not isinstance(item.get("ground_truth_citations", []), list):
        errors.append(f"item {index} ground_truth_citations must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        print("evaluation set must be a list of objects")
        return 1

    errors = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"item {index} must be an object")
            continue
        errors.extend(validate_item(item, index))

    if errors:
        print("validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    output_path = args.output or args.input
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    print(f"validated {len(data)} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
