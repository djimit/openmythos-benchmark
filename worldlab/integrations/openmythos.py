"""OpenMythos taxonomy mapping and trajectory evidence export."""

FAILURE_MAP = {
    "epistemic_contagion": ["hallucination", "calibration", "canary"],
    "emergent_privilege_accumulation": ["tool-scope", "hierarchy"],
    "governance_capture": ["hierarchy", "value-alignment"],
    "correlated_checker_failure": ["calibration", "canary"],
    "memory_poisoning_propagation": ["injection", "hallucination"],
    "delegation_cycle": ["tool-scope", "hierarchy"],
    "policy_drift": ["temporal-reasoning", "value-alignment"],
    "capability_creep": ["tool-scope"],
    "false_consensus": ["hallucination", "calibration"],
    "delayed_policy_violation": ["temporal-reasoning"],
    "recovery_failure": ["temporal-reasoning", "calibration"],
    "institutionalized_hallucination": ["hallucination", "canary", "calibration"],
}
