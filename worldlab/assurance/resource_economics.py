"""Operational resource accounting without virtual currency."""

from __future__ import annotations


def measure_resources(events: list[dict], agents: list[dict]) -> dict:
    metrics = ("events", "tool_calls", "memory_operations", "tokens", "latency_ms", "cost", "context_units")
    by_agent = {agent["id"]: {metric: 0 for metric in metrics} for agent in agents}
    for event in events:
        usage = by_agent.setdefault(event["actor"]["id"], {metric: 0 for metric in metrics})
        evidence = event.get("evidence", {})
        usage["events"] += 1
        usage["tool_calls"] += event["event_type"] in {"tool.executed", "tool.denied"}
        usage["memory_operations"] += event["event_type"] in {"memory.written", "memory.read", "memory.corrected"}
        usage["tokens"] += float(evidence.get("tokens") or 0)
        usage["latency_ms"] += float(evidence.get("latency_ms") or 0)
        usage["cost"] += float(evidence.get("cost") or 0)
        usage["context_units"] += float(evidence.get("context_units") or 0)
    total = sum(item["events"] for item in by_agent.values())
    monopoly = max((item["events"] for item in by_agent.values()), default=0) / max(1, total)
    budget_keys = {
        "tool_calls": ("tool_calls", "tool_call_budget"), "memory_operations": ("memory_budget",),
        "tokens": ("token_budget",), "latency_ms": ("latency_budget_ms", "wall_clock_budget_ms"),
        "context_units": ("context_budget",), "cost": ("compute_budget",),
    }
    violations, utilization = [], {}
    for agent in agents:
        agent_id, budget = agent["id"], agent.get("budget", {})
        utilization[agent_id] = {}
        for metric, aliases in budget_keys.items():
            limit = next((float(budget[key]) for key in aliases if isinstance(budget.get(key), (int, float))), None)
            if limit is None:
                continue
            used = float(by_agent[agent_id][metric])
            utilization[agent_id][metric] = None if limit == 0 else used / limit
            if used > limit:
                violations.append({"agent_id": agent_id, "resource": metric, "used": used, "limit": limit})
    tool_events = [event for event in events if event["event_type"] in {"tool.executed", "tool.denied"}]
    return {
        "by_agent": by_agent, "budget_utilization": utilization, "budget_violations": violations,
        "budget_delegations": sum(event["event_type"] == "budget.delegated" for event in events),
        "resource_monopoly_ratio": monopoly,
        "starved_agents": sorted(agent for agent, usage in by_agent.items() if usage["events"] == 0),
        "inefficient_exploration_rate": sum(event["event_type"] == "tool.denied" for event in tool_events) / max(1, len(tool_events)),
    }
