"""Adversarial review intake; EVE-V is evidence, never the sole oracle."""


def evaluate_challenge(challenge: dict, deterministic_invariants: list[dict]) -> dict:
    false_green = challenge.get("verdict") == "PASS" and any(item["state"] == "FAIL" for item in deterministic_invariants)
    return {
        "source": "EVE-V", "advisory_only": True, "verdict": challenge.get("verdict", "UNDETERMINED"),
        "evidence_gaps": list(challenge.get("evidence_gaps", [])), "contradictions": list(challenge.get("contradictions", [])),
        "false_green": false_green,
        "effective_result": "FAIL" if false_green else challenge.get("verdict", "UNDETERMINED"),
        "hierarchy": ["deterministic_invariant", "oracle", "replicated_statistics", "independent_calibrated_judge", "single_llm_opinion"],
    }
