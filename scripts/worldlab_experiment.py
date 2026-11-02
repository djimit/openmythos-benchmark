#!/usr/bin/env python3
"""Run a replicated WorldLab scenario without production access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.experiment import ExperimentRunner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--replications", type=int)
    parser.add_argument("--models", type=Path, help="Reserved for real-model campaigns; rejected by the synthetic runner")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.models:
        raise SystemExit("real model adapters require an explicitly mediated research campaign")
    scenario = json.loads(args.scenario.read_text())
    report = ExperimentRunner(scenario).run(args.output, args.replications)
    print(json.dumps({"experiment_id": report["experiment_id"], "status": report["status"], "output": str(args.output)}))
    return 0 if report["status"] in {"SUPPORTED", "FALSIFIED", "UNDETERMINED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
