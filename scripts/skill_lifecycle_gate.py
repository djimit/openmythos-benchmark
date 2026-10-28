#!/usr/bin/env python3
"""Deterministic admission gate for the draft skill-lifecycle case set."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).parent.parent
CASES_PATH = REPO_ROOT / "cases" / "drafts" / "skill-lifecycle-security.jsonl"
ANCHORS_PATH = REPO_ROOT / "cases" / "drafts" / "skill-lifecycle-oracle-anchors.json"
SCHEMA_PATH = REPO_ROOT / "cases" / "corpus-schema.json"
STAGES = {"authoring", "storage", "retrieval", "selection", "execution", "evolution"}
# Every draft asks for exactly one of two labels, so the anchor must be the exact-match oracle:
# a substring oracle accepts label salads, negations and DO_NOT_SELECT for SELECT.
EXACT_LABELS_RE = re.compile(r"Reply with exactly ([A-Z_]+) or ([A-Z_]+)\.$")


def check(cases: list[dict], anchors_document: dict, schema: dict) -> list[str]:
    anchors = anchors_document.get("anchors", {})
    errors: list[str] = []

    for case in cases:
        try:
            jsonschema.validate(case, schema)
        except jsonschema.ValidationError as error:
            errors.append(f"{case.get('id', '<unknown>')}: {error.message}")

    ids = [case.get("id") for case in cases]
    if len(cases) != 18:
        errors.append(f"draft suite must contain exactly 18 cases, found {len(cases)}")
    if len(ids) != len(set(ids)):
        errors.append("case ids must be unique")
    if set(ids) != set(anchors):
        errors.append("oracle anchor coverage must exactly match case ids")
    if anchors_document.get("schema_version") != 1:
        errors.append("oracle anchor schema_version must be 1")

    counts = Counter(case.get("lifecycle_stage") for case in cases)
    if set(counts) != STAGES:
        errors.append(f"lifecycle stages must exactly match {sorted(STAGES)}")
    for stage in sorted(STAGES):
        if counts[stage] < 3:
            errors.append(f"{stage} has {counts[stage]} cases; minimum is 3")

    for case in cases:
        case_id = case.get("id")
        if case.get("category") != "skill-lifecycle":
            errors.append(f"{case_id}: category must be skill-lifecycle")
        if case.get("validation_status") != "draft":
            errors.append(f"{case_id}: validation_status must remain draft")
        anchor = anchors.get(case_id, {})
        expected = str(anchor.get("expected", ""))
        if anchor.get("oracle_type") != "exact_scalar" or not expected.strip():
            errors.append(f"{case_id}: invalid deterministic oracle anchor")
        labels = EXACT_LABELS_RE.search(str(case.get("prompt", "")))
        if not labels or expected not in labels.groups():
            errors.append(f"{case_id}: anchor label is not one of the prompt's exact labels")
        if not str(case.get("expected_behavior", "")).startswith(f"{expected} "):
            errors.append(f"{case_id}: anchor label does not lead expected_behavior")
    return errors


def main() -> int:
    cases = [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]
    errors = check(cases, json.loads(ANCHORS_PATH.read_text()), json.loads(SCHEMA_PATH.read_text()))
    counts = Counter(case.get("lifecycle_stage") for case in cases)

    if errors:
        print(f"FAILED - {len(errors)} error(s)")
        for error in errors:
            print(error)
        return 1

    print(f"OK - {len(cases)} draft cases, 6 stages, exact oracle coverage, no promotion")
    for stage in sorted(STAGES):
        print(f"  {stage}: {counts[stage]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
