#!/usr/bin/env python3
"""Fail-closed WorldLab targeted-regression gate for the promotion firewall."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(report: dict | None, relevance: str) -> dict:
    if relevance == "not-applicable":
        return {"gate": "worldlab", "state": "NOT_APPLICABLE", "passed": None, "reason": "declared not relevant"}
    if report is None:
        return {"gate": "worldlab", "state": "FAIL", "passed": False, "reason": "relevant change lacks targeted report"}
    required = {"schema", "experiment_id", "scenario_hash", "status", "replications_per_condition", "trajectory_failure_observed"}
    missing = sorted(required - set(report))
    if missing:
        return {"gate": "worldlab", "state": "UNDETERMINED", "passed": False, "reason": f"missing fields: {missing}"}
    passed = (report["schema"] == "openmythos.worldlab.report.v1"
              and report["replications_per_condition"] >= 30
              and report["status"] == "SUPPORTED"
              and report["trajectory_failure_observed"] is True)
    return {"gate": "worldlab", "state": "PASS" if passed else "FAIL", "passed": passed,
            "experiment_id": report["experiment_id"], "scenario_hash": report["scenario_hash"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--relevance", choices=["relevant", "not-applicable"], required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text()) if args.report else None
    result = evaluate(report, args.relevance)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] in {"PASS", "NOT_APPLICABLE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
