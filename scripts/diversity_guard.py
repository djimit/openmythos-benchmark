#!/usr/bin/env python3
"""Diversity enforcement for OpenMythos case generation.

Prevents clustered, redundant cases by enforcing:
1. Subcategory coverage (no subcategory over-represented)
2. Minimum pairwise distance (character trigram cosine)
3. Difficulty distribution balance
"""
import argparse
import json
import sys
from collections import Counter
from math import sqrt
from pathlib import Path


def trigram_set(text: str) -> set[str]:
    """Extract character trigrams as a cheap semantic proxy."""
    t = text.lower()
    return {t[i:i+3] for i in range(len(t) - 2)} if len(t) >= 3 else {t}


def cosine_similarity(a: set[str], b: set[str]) -> float:
    """Cosine similarity between two sets."""
    if not a or not b: return 0.0
    intersection = len(a & b)
    return intersection / sqrt(len(a) * len(b))


def enforce_diversity(cases: list[dict], min_distance: float = 0.7,
                      max_per_subcategory: int = 3) -> list[dict]:
    """Filter cases to enforce diversity.

    Args:
        cases: list of generated cases
        min_distance: minimum trigram cosine distance (1 - similarity)
        max_per_subcategory: maximum cases per subcategory

    Returns:
        Filtered list with diversity enforced
    """
    selected = []
    subcat_counts = Counter()

    for case in cases:
        subcat = case.get("subcategory", "unknown")
        if subcat_counts[subcat] >= max_per_subcategory:
            continue

        case_trigrams = trigram_set(case.get("prompt", ""))
        is_diverse = True
        for sel in selected:
            sel_trigrams = trigram_set(sel.get("prompt", ""))
            sim = cosine_similarity(case_trigrams, sel_trigrams)
            if sim > (1 - min_distance):
                is_diverse = False
                break

        if is_diverse:
            selected.append(case)
            subcat_counts[subcat] += 1

    excluded = len(cases) - len(selected)
    if excluded > 0:
        print(f"[diversity_guard] Excluded {excluded}/{len(cases)} cases (subcategory cap or similarity)")
    return selected


def balance_difficulty(cases: list[dict], target_per_level: int = 2) -> list[dict]:
    """Ensure balanced difficulty distribution."""
    by_level = {}
    for c in cases:
        d = c.get("difficulty", 3)
        by_level.setdefault(d, []).append(c)

    balanced = []
    for level in sorted(by_level):
        balanced.extend(by_level[level][:target_per_level])

    return balanced


def main():
    parser = argparse.ArgumentParser(description="Enforce diversity in generated cases")
    parser.add_argument("--input", required=True, help="Input JSONL")
    parser.add_argument("--output", required=True, help="Output JSONL")
    parser.add_argument("--min-distance", type=float, default=0.7, help="Min trigram distance")
    parser.add_argument("--max-per-subcat", type=int, default=3, help="Max per subcategory")
    args = parser.parse_args()

    cases = [json.loads(l) for l in Path(args.input).read_text().splitlines() if l.strip()]
    filtered = enforce_diversity(cases, args.min_distance, args.max_per_subcat)
    balanced = balance_difficulty(filtered)

    with open(args.output, 'w') as f:
        for c in balanced:
            f.write(json.dumps(c) + '\n')
    print(f"[diversity_guard] {len(cases)} -> {len(balanced)} cases")


if __name__ == "__main__":
    sys.exit(main())
