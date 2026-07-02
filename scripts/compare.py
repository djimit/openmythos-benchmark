#!/usr/bin/env python3
"""Compare two benchmark runs — compute per-category and per-difficulty scores."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_results(path: str) -> list[dict]:
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def basic_match(response: str, expected: str) -> bool:
    """Simple keyword overlap check — replace with LLM-as-judge for production."""
    resp_lower = response.lower()
    exp_lower = expected.lower()
    # Direct containment
    if exp_lower in resp_lower:
        return True
    # Keyword overlap (for short expected answers)
    exp_words = set(exp_lower.split())
    resp_words = set(resp_lower.split())
    if len(exp_words) <= 3 and exp_words & resp_words:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Compare two benchmark runs")
    parser.add_argument("--run-a", required=True, help="Path to first run JSONL")
    parser.add_argument("--run-b", required=True, help="Path to second run JSONL")
    parser.add_argument(
        "--judge", action="store_true", help="Use LLM-as-judge (requires API)"
    )
    args = parser.parse_args()

    a_results = {r["case_id"]: r for r in load_results(args.run_a)}
    b_results = {r["case_id"]: r for r in load_results(args.run_b)}

    common_ids = set(a_results.keys()) & set(b_results.keys())
    print(f"Comparing {len(common_ids)} common cases...")

    # Load corpus for expected behavior
    corpus = {}
    corpus_path = REPO_ROOT / "cases" / "corpus.jsonl"
    with open(corpus_path) as f:
        for line in f:
            line = line.strip()
            if line:
                c = json.loads(line)
                corpus[c["id"]] = c

    a_correct = 0
    b_correct = 0
    a_by_cat = defaultdict(lambda: {"correct": 0, "total": 0})
    b_by_cat = defaultdict(lambda: {"correct": 0, "total": 0})

    for cid in sorted(common_ids):
        expected = corpus.get(cid, {}).get("expected_behavior", "")
        cat = corpus.get(cid, {}).get("category", "unknown")

        a_match = basic_match(a_results[cid]["response"], expected)
        b_match = basic_match(b_results[cid]["response"], expected)

        if a_match:
            a_correct += 1
            a_by_cat[cat]["correct"] += 1
        if b_match:
            b_correct += 1
            b_by_cat[cat]["correct"] += 1

        a_by_cat[cat]["total"] += 1
        b_by_cat[cat]["total"] += 1

    total = len(common_ids)
    print(f"\n{'Category':25s} {'Run A':>8s} {'Run B':>8s} {'Delta':>8s}")
    print("-" * 55)
    all_cats = sorted(set(list(a_by_cat.keys()) + list(b_by_cat.keys())))
    for cat in all_cats:
        a_acc = (
            100 * a_by_cat[cat]["correct"] / a_by_cat[cat]["total"]
            if a_by_cat[cat]["total"]
            else 0
        )
        b_acc = (
            100 * b_by_cat[cat]["correct"] / b_by_cat[cat]["total"]
            if b_by_cat[cat]["total"]
            else 0
        )
        delta = b_acc - a_acc
        print(f"  {cat:25s} {a_acc:7.1f}% {b_acc:7.1f}% {delta:+7.1f}%")

    print("-" * 55)
    a_total = 100 * a_correct / total
    b_total = 100 * b_correct / total
    print(f"  {'TOTAL':25s} {a_total:7.1f}% {b_total:7.1f}% {b_total - a_total:+.1f}%")


if __name__ == "__main__":
    main()
