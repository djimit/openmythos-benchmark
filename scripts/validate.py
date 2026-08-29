#!/usr/bin/env python3
"""Validate corpus.jsonl against corpus-schema.json plus consistency checks."""

import json
import hashlib
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
MANIFEST_PATH = REPO_ROOT / "cases" / "manifest.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_corpus(corpus_path: Path = CORPUS_PATH) -> list[dict]:
    cases = []
    with open(corpus_path) as f:
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

    # IDs must stay linked to their category, but historical evolution can leave gaps.
    for case in cases:
        prefix = f"{case['category']}-"
        if not case["id"].startswith(prefix):
            errors.append(f"  {case['id']}: id does not start with category prefix {prefix}")

    # At least 25 per category
    from collections import Counter

    cat_counts = Counter(c["category"] for c in cases)
    for cat in expected_cats:
        count = cat_counts.get(cat, 0)
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


def validate_manifest(
    cases: list[dict],
    manifest_path: Path = MANIFEST_PATH,
    require_certification: bool = False,
    corpus_path: Path = CORPUS_PATH,
) -> list[str]:
    if not manifest_path.exists():
        return [f"  Missing corpus manifest: {manifest_path}"]
    manifest = json.loads(manifest_path.read_text())
    errors = []
    if manifest.get("case_count") != len(cases):
        errors.append(f"  Manifest case_count is {manifest.get('case_count')}, expected {len(cases)}")
    digest = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    if manifest.get("sha256") != digest:
        errors.append(f"  Manifest sha256 is {manifest.get('sha256')}, expected {digest}")
    if manifest.get("corpus_path") != "cases/corpus.jsonl":
        errors.append("  Manifest corpus_path must be cases/corpus.jsonl")
    if not isinstance(manifest.get("certification_ready"), bool):
        errors.append("  Manifest certification_ready must be boolean")
    elif require_certification and not manifest["certification_ready"]:
        errors.append("  Corpus is not independently certified for promotion")
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

    all_errors = schema_errors + consistency_errors + validate_manifest(cases)

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
