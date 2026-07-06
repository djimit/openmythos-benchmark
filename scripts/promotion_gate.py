#!/usr/bin/env python3
"""Reject draft cases that add no discriminating benchmark value."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open() as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if "judge_score" not in row:
                    raise SystemExit(f"{path} is missing judge_score")
                rows[row["case_id"]] = row
    return rows


def analyze(traces: dict[str, dict[str, dict]], pass_score: int = 4) -> tuple[list[dict], dict]:
    common = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    rejected = []
    by_category = defaultdict(lambda: {"n": 0, "dead": 0})

    for case_id in common:
        rows = [trace[case_id] for trace in traces.values()]
        scores = [row["judge_score"] for row in rows]
        category = rows[0].get("category", "unknown")
        by_category[category]["n"] += 1
        if max(scores) == min(scores):
            by_category[category]["dead"] += 1
        if max(scores) == min(scores) and scores[0] >= pass_score:
            rejected.append({"case_id": case_id, "category": category, "score": scores[0]})

    categories = {
        category: {
            "n": values["n"],
            "dead_rate": values["dead"] / values["n"] if values["n"] else 0.0,
        }
        for category, values in sorted(by_category.items())
    }
    return rejected, categories


def demo() -> int:
    rejected, categories = analyze(
        {
            "weak": {
                "dead": {"case_id": "dead", "category": "overthinking", "judge_score": 5},
                "good": {"case_id": "good", "category": "overthinking", "judge_score": 2},
            },
            "strong": {
                "dead": {"case_id": "dead", "category": "overthinking", "judge_score": 5},
                "good": {"case_id": "good", "category": "overthinking", "judge_score": 5},
            },
        }
    )
    assert [row["case_id"] for row in rejected] == ["dead"], rejected
    assert categories["overthinking"]["dead_rate"] == 0.5, categories
    print("demo OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="*", type=Path)
    parser.add_argument("--pass-score", type=int, default=4)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return demo()
    if len(args.traces) < 2:
        parser.error("need at least 2 judged traces or --demo")

    traces = {path.stem.replace("judged_", ""): load(path) for path in args.traces}
    rejected, categories = analyze(traces, args.pass_score)

    print("category dead rates:")
    for category, stats in categories.items():
        print(f"  {category}: dead_rate={stats['dead_rate']:.3f} n={stats['n']}")

    if rejected:
        print("\nrejected all-pass dead cases:")
        for row in rejected:
            print(f"  {row['case_id']} ({row['category']}) score={row['score']}")
        return 1

    print("\nOK - no all-pass dead cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
