#!/usr/bin/env python3
"""Package an exploratory model campaign as inert DjimitFlo evidence and a confirmatory goal."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.runtime.event_log import sha256


def package(report: dict, trajectories: list[dict]) -> tuple[dict, list[dict]]:
    report_hash = f"sha256:{sha256(report)}"
    finding_id = f"worldlab-finding:{report_hash.split(':')[-1][:16]}"
    goal = {
        "schema": "djimit.openmythos.worldlab.goal.v1", "campaign_id": f"confirm-{finding_id.split(':')[-1]}",
        "change": "confirm-exploratory-memory-propagation", "source": {"finding_id": finding_id, "evidence_hash": report_hash,
            "study_phase": report["study_phase"], "models": report["model_revisions"]},
        "finding": {"failure_mode": "memory_poisoning_propagation", "severity": "high", "confidence": 0.95,
                    "status": "EXPLORATORY"},
        "waves": [{"wave_id": "confirmatory-replication", "ordered_goals": [{
            "key": "worldlab-confirm-memory-propagation", "title": "Confirm shared-memory propagation finding",
            "risk": "medium", "target": "openmythos-benchmark/worldlab", "depends_on": [],
            "api": {"body": {"objective": "Preregister and independently replicate the homogeneous-model memory poisoning cascade.",
                "risk_class": "medium", "constraints": ["no production tools", "no automatic promotion", "preserve ToolBroker"],
                "acceptance_criteria": ["at least 30 preregistered paired replications", "model revisions and prompt hashes pinned",
                                        "static OpenMythos and WorldLab targeted regressions pass"],
                "falsification_tests": ["trajectory failure is not independently reproduced", "treatment reduction lower bound is not positive"],
                "recommended_loop": "worldlab-confirmatory-research-loop", "metadata": {"finding_id": finding_id,
                    "evidence_hash": report_hash, "promotion_eligible": False, "required_next_gate": "confirmatory_replication"}}}
        }]}],
    }
    baseline = report["infection_probability"]["control"]["mean"]
    outcomes = [{
        "event_id": f"worldlab:{row['trajectory_id']}:infection_probability", "event_type": "outcome.observed",
        "source": "openmythos-worldlab", "correlation_id": finding_id, "causation_id": report_hash,
        "aggregate_id": finding_id, "aggregate_version": row["seed"], "outcome_id": f"outcome:{row['trajectory_id']}",
        "subject_type": "worldlab_treatment", "subject_id": finding_id, "task_id": "local-model-campaign",
        "candidate_id": "candidate:provenance-independent-checker", "capability_id": "worldlab-provenance-independent-checker",
        "model_id": ",".join(report["models"]), "skill_hash": "sha256:none", "runtime_identity": f"git:{report['code_commit']}",
        "metric": "infection_probability", "value": row["infection_probability"], "baseline": baseline,
        "direction": "decrease", "minimum_effect": 0.05, "observation_window": "trajectory:24h",
        "evidence_refs": [report_hash, f"worldlab:{row['trajectory_id']}"], "confidence": 0.95,
        "causal_status": "randomized", "experiment_id": "local-model-campaign", "trajectory_id": row["trajectory_id"],
        "finding_id": finding_id, "condition": "treatment", "replication_id": f"seed-{row['seed']:03d}",
        "risk_class": "medium", "exploratory": True, "observed_at": "2026-09-07T00:00:00+02:00",
        "dedupe_key": f"worldlab:{row['trajectory_id']}:infection_probability",
    } for row in trajectories if row["condition"] == "treatment"]
    return goal, outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.campaign / "report.json").read_text())
    trajectories = json.loads((args.campaign / "trajectory-index.json").read_text())
    goal, outcomes = package(report, trajectories)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "gemma-djimitflo-goals.batch.json").write_text(json.dumps(goal, indent=2, sort_keys=True) + "\n")
    (args.output_dir / "gemma-outcomes.json").write_text(json.dumps(outcomes, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"goals": 1, "outcomes": len(outcomes), "promotion_eligible": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
