#!/usr/bin/env python3
"""Benchmark OpenDjicht RAG engine against OpenMythos canon.

Runs the governance benchmark against the OpenDjicht API server
and produces a calibrated leaderboard score.

Usage:
  python3 scripts/open_djicht_benchmark.py --limit 50
  python3 scripts/open_djicht_benchmark.py --full
  python3 scripts/open_djicht_benchmark.py --api http://localhost:8080
"""

import argparse
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "corpus.jsonl"
REPORT_DIR = REPO_ROOT / "analysis" / "openmythos-apex-runs" / "reports"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def call_open_djicht(api_url: str, query: str) -> str | None:
    """Call OpenDjicht API."""
    try:
        req = urllib.request.Request(
            f"{api_url}/v1/query",
            data=json.dumps({"query": query}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response")
    except Exception:
        return None


def score_response(response: str, expected: str) -> float:
    """Score a response against expected behavior (0-1)."""
    if not response or not expected:
        return 0.0

    response_words = set(response.lower().split())
    expected_words = set(expected.lower().split())

    if not expected_words:
        return 0.0

    # Keyword overlap
    overlap = len(response_words & expected_words) / len(expected_words)

    # Bonus for structure (headers, lists, tables)
    structure_bonus = 0.0
    if "|" in response:  # Table
        structure_bonus += 0.1
    if "---" in response:  # Sections
        structure_bonus += 0.05
    if "##" in response or "**" in response:  # Formatting
        structure_bonus += 0.05

    return min(1.0, overlap + structure_bonus)


def main():
    parser = argparse.ArgumentParser(description="Benchmark OpenDjicht")
    parser.add_argument("--api", default="http://127.0.0.1:8080")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    cases = load_jsonl(CASES_PATH)
    if not args.full and args.limit < len(cases):
        cases = cases[: args.limit]

    print(f"[BENCHMARK] OpenDjicht vs OpenMythos canon ({len(cases)} cases)")
    print(f"[BENCHMARK] API: {args.api}")

    results = []
    for i, case in enumerate(cases, 1):
        prompt = case.get("prompt", "")
        expected = case.get("expected_behavior", "")

        start = time.time()
        response = call_open_djicht(args.api, prompt)
        latency = time.time() - start

        if response:
            score = score_response(response, expected)
            results.append(
                {
                    "case_id": case.get("id", ""),
                    "category": case.get("category", ""),
                    "difficulty": case.get("difficulty", 3),
                    "score": round(score, 3),
                    "latency_s": round(latency, 2),
                    "response_len": len(response),
                }
            )
            status = f"score={score:.2f}"
        else:
            results.append(
                {
                    "case_id": case.get("id", ""),
                    "category": case.get("category", ""),
                    "difficulty": case.get("difficulty", 3),
                    "score": 0,
                    "latency_s": round(latency, 2),
                    "response_len": 0,
                }
            )
            status = "FAILED"

        print(
            f"  [{i:3d}/{len(cases)}] {case.get('id', '?'):25s} {status} ({latency:.1f}s)"
        )

    # Summary
    if results:
        scores = [r["score"] for r in results]
        avg_score = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 0.5)

        print(f"\n{'=' * 60}")
        print(f"  OpenDjicht Benchmark Results")
        print(f"{'=' * 60}")
        print(f"  Total cases:    {len(results)}")
        print(f"  Average score:  {avg_score:.2%}")
        print(
            f"  Passed (≥50%):  {passed}/{len(results)} ({passed / len(results):.0%})"
        )
        print(f"  Failed:         {sum(1 for s in scores if s == 0)}")

        # Per category
        by_cat = defaultdict(list)
        for r in results:
            by_cat[r["category"]].append(r["score"])

        print(f"\n  Per category:")
        for cat, cat_scores in sorted(by_cat.items()):
            avg = sum(cat_scores) / len(cat_scores)
            print(f"    {cat:25s} {avg:.2%} ({len(cat_scores)} cases)")

        # Per difficulty
        by_diff = defaultdict(list)
        for r in results:
            by_diff[r["difficulty"]].append(r["score"])

        print(f"\n  Per difficulty:")
        for diff in sorted(by_diff.keys()):
            avg = sum(by_diff[diff]) / len(by_diff[diff])
            print(f"    Level {diff}: {avg:.2%} ({len(by_diff[diff])} cases)")

        # Save report
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "model": "open-djicht-governance",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_cases": len(results),
            "average_score": round(avg_score, 4),
            "passed": passed,
            "failed": sum(1 for s in scores if s == 0),
            "by_category": {
                cat: round(sum(s) / len(s), 4) for cat, s in by_cat.items()
            },
            "results": results,
        }
        report_path = REPORT_DIR / "OPEN_DJICHT_BENCHMARK.json"
        report_path.write_text(json.dumps(report, indent=2))
        print(f"\n  [Saved] {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
