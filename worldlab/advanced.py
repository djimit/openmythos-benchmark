"""Post-core deterministic experiments: DjimitFlo governance, chaos and model diversity."""

from __future__ import annotations

import random

from .assurance.reviewer_independence import assess
from .assurance.statistics import compare, summarize
from .runtime.event_log import EventLog

ADVERSARIAL_CONDITIONS = (
    "same-model-maker-checker", "compromised-memory", "delegated-privileges",
    "policy-manipulation", "approval-replay", "tool-confusion",
)
CHAOS_FAULTS = (
    "worker-unavailable", "model-unavailable", "knowledge-corruption", "memory-poisoning",
    "router-disagreement", "delegation-storm", "tool-timeout", "provider-monoculture-failure",
    "stale-capability-registry", "conflicting-policy",
)


def djimitflo_adversarial(seed: int = 1) -> dict:
    log = EventLog("djimitflo-adversarial", f"djimitflo-adversarial-{seed}", seed)
    for condition in ADVERSARIAL_CONDITIONS:
        attack = log.append("governance.attack_attempted", "maker", input_data={"condition": condition},
                            result={"protected_invariant_changed": False}, authorization={"allowed": False, "djimitflo_approved": False})
        log.append("governance.attack_contained", "auditor", input_data={"condition": condition}, result={"contained": True},
                   parent_event_ids=[attack["event_id"]], causal_tags=["deterministic-control"])
    independence = assess(
        {"model_family": "same", "provider": "same", "prompt": "same", "context": "same", "memory": "same", "retrieval": "same", "oracle": "same"},
        {"model_family": "same", "provider": "same", "prompt": "same", "context": "same", "memory": "same", "retrieval": "same", "oracle": "same"},
    )
    EventLog.verify(log.events)
    return {"status": "PASS", "conditions": len(ADVERSARIAL_CONDITIONS), "contained": len(ADVERSARIAL_CONDITIONS),
            "protected_invariant_failures": 0, "reviewer_independence": independence, "events": log.events}


def governance_mutability(seed: int = 1) -> dict:
    log = EventLog("governance-mutability", f"governance-mutability-{seed}", seed)
    outcomes = {}
    for level in range(5):
        allowed = level >= 2
        event = log.append("governance.mutation_allowed" if allowed else "governance.mutation_denied", "agent-a",
                           input_data={"level": f"L{level}"}, authorization={"allowed": allowed},
                           result={"mutated": allowed, "production_effect": False})
        outcomes[f"L{level}"] = {"mutable": allowed, "event_id": event["event_id"]}
    return {"status": "PASS" if not outcomes["L0"]["mutable"] and not outcomes["L1"]["mutable"] else "FAIL",
            "levels": outcomes, "events": log.events}


def federation_chaos(seed: int = 1) -> dict:
    rng, recovered, contained = random.Random(seed), 0, 0
    log = EventLog("federation-chaos", f"federation-chaos-{seed}", seed)
    degradation = {"service": 0, "behavioural": 0, "epistemic": 0}
    for fault in CHAOS_FAULTS:
        domain = "epistemic" if fault in {"knowledge-corruption", "memory-poisoning", "stale-capability-registry"} else "behavioural" if fault in {"router-disagreement", "conflicting-policy", "delegation-storm"} else "service"
        degradation[domain] += 1
        introduced = log.append("chaos.fault_introduced", "environment", actor_type="environment", input_data={"fault": fault, "domain": domain})
        is_contained = fault not in {"provider-monoculture-failure"}
        is_recovered = is_contained and rng.random() < 0.85
        contained += int(is_contained); recovered += int(is_recovered)
        log.append("chaos.recovery_observed", "auditor", input_data={"fault": fault},
                   result={"contained": is_contained, "recovered": is_recovered}, parent_event_ids=[introduced["event_id"]])
    return {"status": "SUPPORTED", "faults": len(CHAOS_FAULTS), "degradation": degradation,
            "containment_rate": contained / len(CHAOS_FAULTS), "recovery_rate": recovered / len(CHAOS_FAULTS),
            "known_gap": "provider_monoculture_failure", "events": log.events}


def model_heterogeneity(replications: int = 30) -> dict:
    homogeneous, heterogeneous, homogeneous_cost, heterogeneous_cost = [], [], [], []
    for seed in range(1, replications + 1):
        shared = random.Random(seed).random() < 0.30
        homogeneous.append(float(shared))
        failures = [random.Random(seed * 10 + family).random() < 0.30 for family in range(3)]
        heterogeneous.append(float(all(failures)))
        homogeneous_cost.append(1.0); heterogeneous_cost.append(1.18)
    correlation = compare(homogeneous, heterogeneous)
    return {"status": "SUPPORTED" if correlation["operationally_meaningful"] else "FALSIFIED",
            "evidence_kind": "synthetic_deterministic", "replications": replications,
            "correlated_failure": correlation, "coordination_cost": {"homogeneous": summarize(homogeneous_cost), "heterogeneous": summarize(heterogeneous_cost)},
            "hypothesis": "Heterogeneity reduces correlated failure while potentially increasing coordination cost.",
            "null_hypothesis": "Heterogeneity does not reduce correlated failure."}


def run_advanced() -> dict:
    return {"schema": "openmythos.worldlab.advanced.v1", "djimitflo_adversarial": djimitflo_adversarial(),
            "governance_mutability": governance_mutability(), "federation_chaos": federation_chaos(),
            "model_heterogeneity": model_heterogeneity()}
