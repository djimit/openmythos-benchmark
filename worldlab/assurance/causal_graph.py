"""Provenance graph that never equates temporal order with causality."""


def build_graph(events: list[dict]) -> dict:
    nodes = [{"id": event["event_id"], "type": event["event_type"], "sequence": event["sequence"]} for event in events]
    edges = []
    tags = set()
    for index, event in enumerate(events):
        if index:
            edges.append({"from": events[index - 1]["event_id"], "to": event["event_id"], "relation": "temporal_predecessor", "causal": False})
        for parent in event.get("parent_event_ids", []):
            edges.append({"from": parent, "to": event["event_id"], "relation": "declared_dependency", "causal": False})
        for tag in event.get("causal_tags", []):
            tags.add(tag)
            edges.append({"from": f"tag:{tag}", "to": event["event_id"], "relation": "inferred_causal_relation", "causal": False})
        if event.get("event_type") in {"memory.read", "belief.adopted", "tool.executed", "tool.denied"}:
            for parent in event.get("parent_event_ids", []):
                edges.append({"from": parent, "to": event["event_id"], "relation": "data_dependency", "causal": False})
    nodes.extend({"id": f"tag:{tag}", "type": "causal_tag", "sequence": None} for tag in sorted(tags))
    return {"nodes": nodes, "edges": edges, "experimentally_supported_edges": []}
