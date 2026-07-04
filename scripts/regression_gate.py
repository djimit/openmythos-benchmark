#!/usr/bin/env python3
"""Fail when a judged OpenMythos run regresses against a baseline."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_scores(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if "judge_score" not in row:
                raise SystemExit(f"{path} is missing judge_score; run scripts/judge.py first")
            rows[row["case_id"]] = row
    return rows


def mean(rows: list[dict]) -> float:
    return sum(r["judge_score"] for r in rows) / len(rows) if rows else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate judged benchmark regressions")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--allow-category-regression", action="store_true")
    args = parser.parse_args()

    baseline = load_scores(args.baseline)
    candidate = load_scores(args.candidate)
    common_ids = sorted(set(baseline) & set(candidate))
    if not common_ids:
        raise SystemExit("No common case_id values between baseline and candidate")

    by_category: dict[str, dict[str, list[dict]]] = defaultdict(lambda: {"base": [], "cand": []})
    base_rows = []
    cand_rows = []
    regressions = []

    for case_id in common_ids:
        b = baseline[case_id]
        c = candidate[case_id]
        base_rows.append(b)
        cand_rows.append(c)
        category = c.get("category") or b.get("category") or "unknown"
        by_category[category]["base"].append(b)
        by_category[category]["cand"].append(c)
        if c["judge_score"] < b["judge_score"]:
            regressions.append((case_id, category, b["judge_score"], c["judge_score"]))

    base_mean = mean(base_rows)
    cand_mean = mean(cand_rows)
    delta = cand_mean - base_mean

    print(f"cases={len(common_ids)} baseline={base_mean:.3f} candidate={cand_mean:.3f} delta={delta:+.3f}")
    print(f"{'category':25s} {'base':>7s} {'cand':>7s} {'delta':>8s}")
    for category in sorted(by_category):
        b = mean(by_category[category]["base"])
        c = mean(by_category[category]["cand"])
        print(f"{category:25s} {b:7.3f} {c:7.3f} {c - b:+8.3f}")

    failed = delta < args.min_delta
    if not args.allow_category_regression:
        for category, rows in by_category.items():
            if mean(rows["cand"]) < mean(rows["base"]):
                failed = True

    if regressions:
        print("\ncase regressions:")
        for case_id, category, b, c in regressions[:20]:
            print(f"  {case_id:20s} {category:25s} {b} -> {c}")
        if len(regressions) > 20:
            print(f"  ... {len(regressions) - 20} more")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
