"""Deterministic replay of DjimitFlo social-learning evidence."""

from __future__ import annotations

from pathlib import Path

from .runtime.event_log import EventLog, sha256
from .runtime.replay import counterfactual_replay, replay
from .runtime.world_state import empty_state


def replay_campaign(payload: dict, source_commit: str, traces_dir: Path | None = None) -> dict:
    if payload.get("schema") != "djimit.social-learning-campaign.worldlab-input.v1":
        raise ValueError("invalid social-learning campaign input schema")
    campaign_id = payload.get("campaign_id")
    if not isinstance(campaign_id, str) or not campaign_id or not source_commit:
        raise ValueError("campaign_id and source_commit are required")
    pairs = payload.get("pairs")
    if not isinstance(pairs, list):
        raise ValueError("campaign pairs must be a list")

    trajectories, failures = [], []
    for index, pair in enumerate(pairs, 1):
        if not isinstance(pair, dict):
            failures.append(f"pair-{index}:invalid")
            continue
        required = ("thread_id", "agent_id", "peer_agent_id", "baseline_hash", "peer_hash", "learning_hash")
        missing = [field for field in required if not isinstance(pair.get(field), str) or not pair[field]]
        if missing:
            failures.append(f"pair-{index}:missing:{','.join(missing)}")
            continue
        if pair["agent_id"] == pair["peer_agent_id"] or pair.get("effect_scope") != "isolated":
            failures.append(f"pair-{index}:containment_or_independence")
            continue
        trajectory_id = f"{campaign_id}-pair-{index:04d}"
        log = EventLog(campaign_id, trajectory_id, index)
        baseline = log.append(
            "social.baseline_observed", pair["agent_id"],
            result={"response_hash": pair["baseline_hash"]},
            state_delta={"set": [{"domain": "knowledge", "key": pair["agent_id"], "value": pair["baseline_hash"]}]},
            evidence={"message_id": pair.get("baseline_message_id")},
        )
        exposure = log.append(
            "social.peer_feedback_exposed", pair["peer_agent_id"],
            result={"peer_hash": pair["peer_hash"], "effect_scope": "isolated"},
            state_delta={"set": [{"domain": "relationships", "key": pair["thread_id"], "value": {"peer_exposed": True}}]},
            parent_event_ids=[baseline["event_id"]], causal_tags=["declared_dependency"],
            evidence={"message_id": pair.get("peer_message_id")},
        )
        learning = log.append(
            "social.learning_observed", pair["agent_id"],
            result={"learning_hash": pair["learning_hash"]},
            state_delta={"set": [{"domain": "knowledge", "key": pair["agent_id"], "value": pair["learning_hash"]}]},
            parent_event_ids=[exposure["event_id"]], causal_tags=["temporal_predecessor", "declared_dependency"],
            evidence={"message_id": pair.get("learning_message_id"), "reflection_id": pair.get("reflection_id")},
        )
        events = log.events
        observed = replay(empty_state(), events)
        counterfactual = counterfactual_replay(
            empty_state(), events, 2,
            {"set": [{"domain": "knowledge", "key": pair["agent_id"], "value": pair["baseline_hash"]}]},
        )
        valid = observed["knowledge"].get(pair["agent_id"]) == pair["learning_hash"] \
            and counterfactual["counterfactual_final_state"]["knowledge"].get(pair["agent_id"]) == pair["baseline_hash"] \
            and counterfactual["causal_claim_supported"] is False
        if not valid:
            failures.append(f"pair-{index}:replay_mismatch")
        if traces_dir:
            log.write_jsonl(traces_dir / f"{trajectory_id}.jsonl")
        trajectories.append({
            "trajectory_id": trajectory_id, "thread_id": pair["thread_id"], "agent_id": pair["agent_id"],
            "observed_learning_hash": pair["learning_hash"], "counterfactual_learning_hash": pair["baseline_hash"],
            "intervention_event": learning["event_id"], "replay_exact": valid,
            "causal_claim_supported": False, "event_chain_hash": events[-1]["event_hash"],
        })

    core = {
        "schema": "openmythos.worldlab.social-learning-replay.v1", "campaign_id": campaign_id,
        "status": "PASS" if trajectories and not failures else "FAIL" if failures else "UNDETERMINED",
        "source_commit": source_commit, "input_report_hash": payload.get("report_hash"),
        "trajectories": len(trajectories), "failures": failures,
        "causal_claim_supported": False,
        "interpretation": "Replay verifies lineage and intervention mechanics; it does not establish that peer feedback caused a better real-world outcome.",
    }
    return {**core, "evidence_hash": f"sha256:{sha256(core)}", "trajectory_index": trajectories}
