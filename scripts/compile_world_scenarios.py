#!/usr/bin/env python3
"""Compile eligible pointwise OpenMythos cases into longitudinal scenario templates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worldlab.experiment import validate_scenario
from worldlab.runtime.world_state import empty_state

FAMILIES = {
    "injection": "epistemic-propagation", "canary": "epistemic-propagation",
    "tool-scope": "capability-delegation", "hierarchy": "governance-capture",
    "hallucination": "epistemic-contagion", "calibration": "checker-correlation",
    "temporal-reasoning": "recovery",
}


def compile_case(case: dict) -> dict | None:
    metadata = case.get("worldlab", {})
    eligible = metadata.get("eligible", case.get("category") in FAMILIES)
    if not eligible:
        return None
    family = metadata.get("scenario_family", FAMILIES.get(case["category"], "longitudinal"))
    model = {"provider": "synthetic", "model": "case-adapter", "version": "1", "temperature": 0,
             "seed": 1, "system_prompt_hash": f"case:{case['id']}", "toolset_hash": "synthetic:none", "context_hash": f"case:{case['id']}"}
    return {
        "id": f"wl-{family}-{case['id']}", "version": "1.0",
        "research_question": f"Does {case['failure_mode']} emerge through interaction over time?",
        "hypothesis": f"Longitudinal interaction exposes {case['failure_mode']} not visible pointwise.",
        "null_hypothesis": "The longitudinal condition adds no detectable failure.",
        "openmythos_categories": [case["category"]], "initial_state": empty_state(),
        "agents": [{"id": "agent-a", "model": model, "role": "case subject", "initial_capabilities": [],
                    "memory_scope": ["private", "shared"], "authority": [], "objectives": [case["expected_behavior"]],
                    "constraints": ["worldlab only"], "budget": {"events": 100}}],
        "capabilities": [], "memory_topology": {"private": True, "shared": True, "anonymous_writes": False},
        "governance": {"external_side_effects": False}, "perturbations": [{"type": family, "prompt": case["prompt"]}],
        "invariants": [{"id": "no-side-effect", "kind": "always", "predicate": "no_external_side_effect"}],
        "forbidden_states": [case["failure_mode"]], "observation_window": {"events": 100}, "replications": 30,
        "randomization": {"paired_seed_set": True}, "expected_properties": [case["expected_behavior"]],
        "falsification_conditions": ["no difference from pointwise control"], "oracle_strategy": {"source_case": case["id"]},
        "independent_variables": ["interaction and memory"], "dependent_variables": ["invariant violation frequency"],
        "controls": ["pointwise source case"], "confounders": ["synthetic adapter"], "stopping_condition": "30 replications",
        "analysis_method": "Paired trajectory comparison.", "limitations": ["Template requires family-specific perturbation logic."],
        "source_case": {"id": case["id"], "version": case["version"], "failure_mode": case["failure_mode"]}, "status": "DRAFT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("cases/corpus.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    compiled = 0
    args.output.mkdir(parents=True, exist_ok=True)
    for line in args.corpus.read_text().splitlines():
        scenario = compile_case(json.loads(line))
        if scenario is None:
            continue
        validate_scenario(scenario)
        (args.output / f"{scenario['id']}.json").write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n")
        compiled += 1
        if args.limit and compiled >= args.limit:
            break
    print(json.dumps({"compiled": compiled, "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
