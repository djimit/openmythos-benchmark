#!/usr/bin/env python3
"""Validate any JSONL file against a JSON Schema."""

import argparse
import json
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument(
        "--schema", type=Path, default=REPO_ROOT / "cases" / "corpus-schema.json"
    )
    args = parser.parse_args()

    schema = json.loads(args.schema.read_text())
    errors = []
    rows = 0
    with args.jsonl.open() as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
                jsonschema.validate(row, schema)
            except Exception as e:
                errors.append(f"line {line_no}: {e}")

    if errors:
        print(f"FAILED - {len(errors)} error(s)")
        for error in errors:
            print(error)
        return 1

    print(f"OK - {rows} row(s) valid against {args.schema}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
