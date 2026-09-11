"""Deterministic and counterfactual WorldLab replay."""

from __future__ import annotations

import copy

from .event_log import EventLog
from .world_state import WorldState


def replay(initial_state: dict, events: list[dict], until: int | None = None) -> dict:
    EventLog.verify(events)
    state = WorldState(initial_state)
    for event in events[:until]:
        state.apply(event.get("state_delta", {}))
    return state.snapshot()


def counterfactual_replay(
    initial_state: dict,
    events: list[dict],
    replace_at: int,
    replacement_delta: dict | None = None,
    *,
    replacement_event: dict | None = None,
) -> dict:
    """Intervene at one event; returns evidence, never an automatic causal claim."""
    EventLog.verify(events)
    if replace_at < 0 or replace_at >= len(events):
        raise IndexError("counterfactual event outside trajectory")
    changed = copy.deepcopy(events)
    if replacement_delta is None and replacement_event is None:
        raise ValueError("counterfactual replay requires an intervention")
    intervention_fields = {"actor", "intent", "input", "authorization", "result", "state_delta", "causal_tags", "evidence"}
    if replacement_event:
        unknown = set(replacement_event) - intervention_fields
        if unknown:
            raise ValueError(f"counterfactual cannot replace event identity fields: {sorted(unknown)}")
        changed[replace_at].update(copy.deepcopy(replacement_event))
    if replacement_delta is not None:
        changed[replace_at]["state_delta"] = copy.deepcopy(replacement_delta)
    # The intervention intentionally invalidates the observed hash chain, so replay
    # applies deltas directly and labels the result as counterfactual evidence.
    state = WorldState(initial_state)
    for event in changed:
        state.apply(event.get("state_delta", {}))
    return {
        "kind": "counterfactual",
        "intervention_event": events[replace_at]["event_id"],
        "intervention_fields": sorted(set(replacement_event or {}) | ({"state_delta"} if replacement_delta is not None else set())),
        "observed_final_state": replay(initial_state, events),
        "counterfactual_final_state": state.snapshot(),
        "causal_claim_supported": False,
    }
