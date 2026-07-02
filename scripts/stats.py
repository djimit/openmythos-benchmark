#!/usr/bin/env python3
"""Descriptive statistics for the OpenMythos benchmark corpus."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"


def main():
    cases = []
    with open(CORPUS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    total = len(cases)
    cats = Counter(c["category"] for c in cases)
    diffs = Counter(c["difficulty"] for c in cases)
    subcats = Counter(c["subcategory"] for c in cases)
    loop_true = sum(1 for c in cases if c["loop_sensitive"])
    statuses = Counter(c["validation_status"] for c in cases)

    # Prompt length stats
    prompt_lens = [len(c["prompt"]) for c in cases]
    expected_lens = [len(c["expected_behavior"]) for c in cases]

    # References
    total_refs = sum(len(c["references"]) for c in cases)
    refs_per_case = Counter(len(c["references"]) for c in cases)

    print("=" * 60)
    print(f"OpenMythos Governance Benchmark Corpus Statistics")
    print("=" * 60)
    print(f"\nTotal cases: {total}")
    print(f"Categories: {len(cats)}")
    print(f"Unique subcategories: {len(subcats)}")
    print(f"Loop-sensitive: {loop_true} ({100 * loop_true / total:.0f}%)")
    print(f"Total references: {total_refs} (avg {total_refs / total:.1f}/case)")

    print(f"\n--- Cases per category ---")
    for cat, count in sorted(cats.items()):
        print(f"  {cat:25s} {count:3d}")

    print(f"\n--- Difficulty distribution ---")
    for d in sorted(diffs):
        bar = "█" * diffs[d]
        print(f"  Level {d}: {diffs[d]:3d} {bar}")

    print(f"\n--- Validation status ---")
    for status, count in sorted(statuses.items()):
        print(f"  {status:15s} {count:3d}")

    print(f"\n--- Prompt length ---")
    print(f"  Min: {min(prompt_lens)}")
    print(f"  Max: {max(prompt_lens)}")
    print(f"  Avg: {sum(prompt_lens) / len(prompt_lens):.0f}")
    print(f"  Median: {sorted(prompt_lens)[len(prompt_lens) // 2]}")

    print(f"\n--- Expected behavior length ---")
    print(f"  Min: {min(expected_lens)}")
    print(f"  Max: {max(expected_lens)}")
    print(f"  Avg: {sum(expected_lens) / len(expected_lens):.0f}")

    print(f"\n--- References per case ---")
    for n, count in sorted(refs_per_case.items()):
        print(f"  {n} refs: {count} cases")

    # Category × difficulty matrix
    print(f"\n--- Category × Difficulty ---")
    print(f"  {'':25s} ", end="")
    for d in range(1, 6):
        print(f"  L{d}", end="")
    print()
    for cat in sorted(cats):
        print(f"  {cat:25s} ", end="")
        for d in range(1, 6):
            count = sum(
                1 for c in cases if c["category"] == cat and c["difficulty"] == d
            )
            print(f"  {count:2d}", end="")
        print()


if __name__ == "__main__":
    main()
