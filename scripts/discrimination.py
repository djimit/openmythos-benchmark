#!/usr/bin/env python3
"""Measure how well a corpus version discriminates model quality.

A governance benchmark is *better* when it separates strong models from weak
ones and wastes few cases on which every model scores the same. Feed it >=2
judged traces (same corpus, different models) and it reports:

  - per-model average judged score
  - discrimination = best-model avg minus worst-model avg (overall + per category)
  - dead-case rate: share of cases where every model got the identical score
    (no discriminating power — candidates to cut or harden)

To prove version N+1 beats version N: run this on both corpora with the same
model set. Higher discrimination and a lower dead-case rate = a better corpus.

Usage:
  python3 scripts/discrimination.py judged_opus.jsonl judged_qwen.jsonl judged_llama.jsonl
  python3 scripts/discrimination.py --demo   # self-check
"""

import argparse
import json
import sys
from collections import defaultdict


def load(path):
    """Return {case_id: {"score": int, "category": str}} from a judged trace."""
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[r["case_id"]] = {
                "score": r["judge_score"],
                "category": r.get("category", "?"),
            }
    return out


def analyze(traces: dict) -> dict:
    """traces: {model_name: {case_id: {score, category}}}. Returns a report dict."""
    models = list(traces)
    # cases scored by every model (fair comparison set)
    common = set.intersection(*(set(t) for t in traces.values()))

    per_model = {m: _mean(traces[m][c]["score"] for c in common) for m in models}

    # per-category discrimination + dead cases
    by_cat = defaultdict(lambda: {"spread": [], "dead": 0, "n": 0})
    dead_total = 0
    for c in common:
        scores = [traces[m][c]["score"] for m in models]
        cat = traces[models[0]][c]["category"]
        by_cat[cat]["n"] += 1
        by_cat[cat]["spread"].append(max(scores) - min(scores))
        if max(scores) == min(scores):
            by_cat[cat]["dead"] += 1
            dead_total += 1

    cat_report = {
        cat: {
            "avg_spread": round(_mean(v["spread"]), 3),
            "dead_rate": round(v["dead"] / v["n"], 3),
            "n": v["n"],
        }
        for cat, v in sorted(by_cat.items())
    }

    return {
        "n_cases": len(common),
        "per_model_avg": {m: round(s, 3) for m, s in per_model.items()},
        "discrimination": round(max(per_model.values()) - min(per_model.values()), 3),
        "dead_case_rate": round(dead_total / len(common), 3),
        "per_category": cat_report,
    }


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _print(report):
    print(f"\ncases compared (scored by all models): {report['n_cases']}")
    print("\nper-model average judged score:")
    for m, s in sorted(report["per_model_avg"].items(), key=lambda kv: -kv[1]):
        print(f"  {m:<28} {s:.3f}")
    print(f"\ndiscrimination (best - worst): {report['discrimination']:.3f}  (higher = better corpus)")
    print(f"dead-case rate:                {report['dead_case_rate']:.3f}  (lower = better corpus)")
    print("\nper category (avg spread / dead rate):")
    for cat, v in report["per_category"].items():
        print(f"  {cat:<20} spread={v['avg_spread']:.2f}  dead={v['dead_rate']:.2f}  n={v['n']}")


def _demo():
    """Self-check: a corpus that separates a strong from a weak model scores
    higher discrimination and a lower dead-case rate than one that doesn't."""
    strong = {f"c{i}": {"score": 5, "category": "injection"} for i in range(10)}
    weak_good = {f"c{i}": {"score": 2, "category": "injection"} for i in range(10)}
    weak_dead = {f"c{i}": {"score": 5, "category": "injection"} for i in range(10)}

    discriminating = analyze({"strong": strong, "weak": weak_good})
    useless = analyze({"strong": strong, "weak": weak_dead})

    assert discriminating["discrimination"] == 3.0, discriminating
    assert discriminating["dead_case_rate"] == 0.0, discriminating
    assert useless["discrimination"] == 0.0, useless
    assert useless["dead_case_rate"] == 1.0, useless
    print("demo OK: discriminating corpus scores 3.0 spread / 0.0 dead; "
          "useless corpus scores 0.0 / 1.0")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("traces", nargs="*", help="Two or more judged JSONL traces")
    p.add_argument("--demo", action="store_true", help="Run self-check and exit")
    args = p.parse_args()

    if args.demo:
        _demo()
        return
    if len(args.traces) < 2:
        p.error("need at least 2 judged traces (or --demo)")

    traces = {}
    for path in args.traces:
        name = path.rsplit("/", 1)[-1].replace("judged_", "").replace(".jsonl", "")
        traces[name] = load(path)
    _print(analyze(traces))


if __name__ == "__main__":
    sys.exit(main())
