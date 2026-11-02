#!/usr/bin/env python3
"""Run deterministic post-core WorldLab experiments."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.advanced import run_advanced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_advanced()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value.get("status") for key, value in result.items() if isinstance(value, dict)}))
    return 0 if all(value.get("status") in {"PASS", "SUPPORTED"} for value in result.values() if isinstance(value, dict)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
