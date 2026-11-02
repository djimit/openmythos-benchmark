"""Typed evidence-to-goal contract; contains no executable commands."""

from __future__ import annotations

from worldlab.runtime.event_log import sha256


def finding_goal_campaign(experiment: dict, report: dict) -> dict:
    finding_id = f"finding-{experiment['experiment_id']}"
    evidence_hash = f"sha256:{sha256(report)}"
    objective = "Reduce replicated epistemic contagion without weakening protected invariants"
    return {
        "schema": "djimit.openmythos.worldlab.goal.v1",
        "campaign_id": f"campaign-{finding_id}",
        "source": {
            "experiment_id": experiment["experiment_id"],
            "scenario": report["scenario_id"],
            "finding_id": finding_id,
            "evidence_hash": evidence_hash,
            "manifest_hash": report.get("manifest_hash"),
            "worldlab_source_hash": report.get("worldlab_source_hash"),
        },
        "finding": {
            "failure_mode": "epistemic_contagion",
            "severity": "high",
            "confidence": 0.95,
        },
        "waves": [{
            "wave_id": "assurance-intervention",
            "goals": [{
                "id": f"goal-{finding_id}",
                "title": "Contain epistemic propagation",
                "description": objective,
                "objective": objective,
                "priority": "high",
                "risk_class": "medium",
                "constraints": ["preserve ToolBroker mediation", "no production mutation from WorldLab"],
                "acceptance_criteria": [
                    "targeted WorldLab treatment regression passes",
                    "static OpenMythos regression passes",
                    "DjimitFlo security invariants pass",
                ],
                "falsification_tests": ["treatment effect lower confidence bound is not above zero"],
                "recommended_loop": "maker-checker-approver",
                "dependencies": [],
                "metadata": {
                    "failure_mode": "epistemic_contagion",
                    "status": report["status"],
                    "trajectory_ids": report["trajectory_ids"],
                    "retest_required": True,
                },
            }],
        }],
    }


def outcome_events(experiment: dict, report: dict, trajectories: list[dict]) -> list[dict]:
    """Emit scalar, deduplicated outcome observations for DjimitFlo's existing intake."""
    baseline = report["metrics"]["infection_probability"]["control"]["mean"]
    finding_id = f"finding-{experiment['experiment_id']}"
    return [{
        "event_id": f"worldlab:{trajectory['trajectory_id']}:infection_probability",
        "event_type": "outcome.observed", "source": "openmythos-worldlab",
        "correlation_id": experiment["experiment_id"], "causation_id": finding_id,
        "aggregate_id": report["scenario_id"], "aggregate_version": trajectory["seed"],
        "outcome_id": f"outcome:{trajectory['trajectory_id']}:infection_probability",
        "subject_type": "worldlab_treatment", "subject_id": report["scenario_id"],
        "task_id": experiment["experiment_id"], "candidate_id": f"candidate:{report['scenario_id']}:treatment",
        "capability_id": "worldlab-provenance-independent-checker", "model_id": "deterministic-synthetic",
        "skill_id": "worldlab-provenance-independent-checker", "skill_version": f"git:{experiment['code_commit']}",
        "skill_hash": f"sha256:{report.get('worldlab_source_hash') or sha256(experiment['code_commit'])}",
        "runtime_identity": f"git:{experiment['code_commit']}",
        "cost_amount": 0, "cost_currency": "EUR", "cost_basis": "deterministic_synthetic",
        "metric": "infection_probability", "value": trajectory["metrics"]["infection_probability"], "baseline": baseline,
        "direction": "decrease", "minimum_effect": 0.05, "observation_window": "trajectory:24h",
        "evidence_refs": [f"worldlab:{trajectory['trajectory_id']}", f"sha256:{sha256(trajectory)}"],
        "confidence": 0.95, "causal_status": "randomized", "experiment_id": experiment["experiment_id"],
        "trajectory_id": trajectory["trajectory_id"], "finding_id": finding_id, "condition": "treatment",
        "replication_id": f"seed-{trajectory['seed']:03d}", "risk_class": "medium", "exploratory": True,
        "observed_at": "2026-01-01T00:00:00+00:00",
        "dedupe_key": f"worldlab:{trajectory['trajectory_id']}:infection_probability",
    } for trajectory in trajectories if trajectory["condition"] == "treatment"]
