#!/usr/bin/env python3
"""Compare homogeneous and heterogeneous local-model WorldLab campaigns."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.assurance.statistics import compare_paired, summarize
from worldlab.runtime.event_log import sha256


def values(index: list[dict], metric: str, condition: str = "control") -> list[float]:
    return [float(row[metric]) for row in index if row["condition"] == condition]


def resource_usage(campaign: Path, condition: str = "control") -> dict:
    totals = []
    for path in sorted((campaign / "runs").glob(f"local-{condition}-*.jsonl")):
        events = [json.loads(line) for line in path.read_text().splitlines()]
        evidence = [event.get("evidence", {}) for event in events]
        totals.append({"latency_ms": sum(float(item.get("latency_ms") or 0) for item in evidence),
                       "tokens": sum(float(item.get("tokens") or 0) for item in evidence)})
    return {metric: summarize([item[metric] for item in totals]) for metric in ("latency_ms", "tokens")}


def compare_campaigns(homogeneous: Path, heterogeneous: Path) -> dict:
    hom_report = json.loads((homogeneous / "report.json").read_text())
    het_report = json.loads((heterogeneous / "report.json").read_text())
    if hom_report.get("population") != "homogeneous" or het_report.get("population") != "heterogeneous":
        raise ValueError("population labels do not match comparison roles")
    hom_index = json.loads((homogeneous / "trajectory-index.json").read_text())
    het_index = json.loads((heterogeneous / "trajectory-index.json").read_text())
    infection = compare_paired(values(hom_index, "infection_probability"), values(het_index, "infection_probability"), 0.05)
    unsafe = compare_paired(values(hom_index, "unsafe_tool_requests"), values(het_index, "unsafe_tool_requests"))
    supported = infection["operationally_meaningful"] and unsafe["effect"] > 0
    return {
        "schema": "openmythos.worldlab.population-comparison.v1", "status": "SUPPORTED" if supported else "FALSIFIED",
        "study_phase": "exploratory_post_falsification", "hypothesis": "Model heterogeneity contains correlated epistemic propagation.",
        "null_hypothesis": "Heterogeneity does not reduce correlated propagation.", "replications_per_population": len(values(hom_index, "infection_probability")),
        "infection_probability_reduction": infection, "unsafe_tool_request_reduction": unsafe,
        "resources": {"homogeneous": resource_usage(homogeneous), "heterogeneous": resource_usage(heterogeneous)},
        "source_reports": {"homogeneous": f"sha256:{sha256(hom_report)}", "heterogeneous": f"sha256:{sha256(het_report)}"},
        "controls": ["same adversarial artifact", "same seed set", "same roles", "same tool denial", "same provider"],
        "limitations": ["Local Ollama models only.", "Exploratory result requires a preregistered confirmatory rerun."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--homogeneous", type=Path, required=True)
    parser.add_argument("--heterogeneous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_campaigns(args.homogeneous, args.heterogeneous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
