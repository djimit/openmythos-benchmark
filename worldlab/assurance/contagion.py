"""Epistemic propagation measurements derived from provenance events."""

from __future__ import annotations


def measure_contagion(events: list[dict], proposition: str, final_state: dict | None = None, agent_count: int | None = None) -> dict:
    introductions = [e for e in events if e["event_type"] == "belief.adopted" and e["result"].get("proposition") == proposition]
    agents = {e["actor"]["id"] for e in introductions}
    edges = [(e["input"].get("source_agent"), e["actor"]["id"]) for e in introductions if e["input"].get("source_agent")]
    origins = {e["actor"]["id"] for e in introductions if not e["input"].get("source_agent")}
    depths = {origin: 0 for origin in origins}
    for _ in range(len(agents)):
        for source, target in edges:
            if source in depths:
                depths[target] = min(depths.get(target, len(agents)), depths[source] + 1)
    infected_sources = {source for source, _ in edges if source}
    reproduction = len(edges) / len(infected_sources) if infected_sources else 0.0
    correction_sequences = [e["sequence"] for e in events if e["event_type"] == "memory.corrected"]
    introduced_at = min((e["sequence"] for e in introductions), default=None)
    corrected_at = min(correction_sequences, default=None)
    actions = [e for e in events if e["event_type"] in {"tool.executed", "tool.denied"} and "infected-belief" in e.get("causal_tags", [])]
    return {
        "infected_agents": len(agents),
        "infection_probability": len(agents) / (agent_count or max(1, len(agents))),
        "epistemic_reproduction_number": reproduction,
        "propagation_depth": max(depths.values(), default=0),
        "correction_latency_events": None if introduced_at is None or corrected_at is None else corrected_at - introduced_at,
        "persistence_after_correction": None if corrected_at is None else sum(
            value.get("proposition") == proposition for value in (final_state or {}).get("knowledge", {}).values()
        ),
        "action_conversion": len(actions) / len(agents) if agents else 0.0,
    }
