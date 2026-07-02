#!/usr/bin/env python3
"""Validate corpus.jsonl against corpus-schema.json plus consistency checks."""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. pip install jsonschema")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SCHEMA_PATH = REPO_ROOT / "cases" / "corpus-schema.json"
CORPUS_PATH = REPO_ROOT / "cases" / "corpus.jsonl"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_corpus() -> list[dict]:
    cases = []
    with open(CORPUS_PATH) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON at line {line_no}: {e}")
                sys.exit(1)
    return cases


def validate_schema(cases: list[dict], schema: dict) -> list[str]:
    errors = []
    for i, case in enumerate(cases):
        try:
            jsonschema.validate(case, schema)
        except jsonschema.ValidationError as e:
            case_id = case.get("id", f"line_{i + 1}")
            errors.append(f"  {case_id}: {e.message} ({e.json_path})")
    return errors


def validate_consistency(cases: list[dict]) -> list[str]:
    errors = []
    ids = [c["id"] for c in cases]

    # Unique IDs
    seen = set()
    for cid in ids:
        if cid in seen:
            errors.append(f"  Duplicate id: {cid}")
        seen.add(cid)

    # Sequential numbering per category
    from collections import defaultdict

    cat_counts = defaultdict(list)
    for cid in ids:
        parts = cid.rsplit("-", 1)
        if len(parts) == 2:
            cat_counts[parts[0]].append(int(parts[1]))

    for cat, nums in sorted(cat_counts.items()):
        expected = list(range(1, len(nums) + 1))
        sorted_nums = sorted(nums)
        if sorted_nums != expected:
            errors.append(f"  {cat}: non-sequential IDs {sorted_nums}")

    # Categories present
    expected_cats = {
        "hierarchy",
        "injection",
        "tool-scope",
        "contradiction",
        "canary",
        "overthinking",
        "hallucination",
        "calibration",
        "value-alignment",
        "temporal-reasoning",
        "cross-lingual",
    }
    actual_cats = set(c["category"] for c in cases)
    missing = expected_cats - actual_cats
    if missing:
        errors.append(f"  Missing categories: {missing}")
    extra = actual_cats - expected_cats
    if extra:
        errors.append(f"  Unknown categories: {extra}")

    # At least 25 per category
    for cat in expected_cats:
        count = len(cat_counts.get(cat, []))
        if count < 25:
            errors.append(f"  {cat}: only {count} cases (min 25)")

    # References required and non-empty
    for case in cases:
        refs = case.get("references", [])
        if not refs:
            errors.append(f"  {case['id']}: no references")
        for ref in refs:
            if not ref.get("title") or not ref.get("url_or_doi"):
                errors.append(f"  {case['id']}: incomplete reference")

    return errors


def main():
    if not CORPUS_PATH.exists():
        print(f"ERROR: {CORPUS_PATH} not found")
        sys.exit(1)

    schema = load_schema()
    cases = load_corpus()

    print(f"Validating {len(cases)} cases...")

    schema_errors = validate_schema(cases, schema)
    consistency_errors = validate_consistency(cases)

    all_errors = schema_errors + consistency_errors

    if all_errors:
        print(f"\nFAILED — {len(all_errors)} error(s):\n")
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print(f"OK — all {len(cases)} cases valid.")
        from collections import Counter

        cats = Counter(c["category"] for c in cases)
        for cat, count in sorted(cats.items()):
            print(f"  {cat}: {count}")
        print(f"  TOTAL: {len(cases)}")


if __name__ == "__main__":
    main()
