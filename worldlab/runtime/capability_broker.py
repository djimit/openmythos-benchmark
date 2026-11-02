"""Simulated capability reference monitor; never calls production tools."""

from __future__ import annotations

from .event_log import EventLog
from .world_state import WorldState


class WorldLabCapabilityBroker:
    def __init__(self, state: WorldState, log: EventLog, allowed: set[str]) -> None:
        self.state = state
        self.log = log
        self.allowed = allowed

    def effective(self, agent_id: str) -> set[str]:
        capabilities = self.state.snapshot()["capabilities"]
        direct = set(capabilities.get(agent_id, {}).get("authorized", []))
        delegated = {
            edge["capability"] for edge in capabilities.get("delegations", [])
            if edge["to"] == agent_id and not edge.get("revoked", False)
        }
        return direct | delegated

    def delegate(self, source: str, target: str, capability: str) -> dict:
        permitted = capability in self.effective(source)
        delta = {}
        if permitted:
            delta = {"append": [{"domain": "capabilities", "key": "delegations", "value": {
                "from": source, "to": target, "capability": capability, "revoked": False,
            }}]}
            self.state.apply(delta)
        return self.log.append(
            "capability.delegated" if permitted else "capability.delegation_denied",
            source,
            intent={"target": target, "capability": capability},
            authorization={"allowed": permitted}, result={"delegated": permitted}, state_delta=delta,
        )

    def request(self, agent_id: str, capability: str, *, parent_event_ids: list[str] | None = None,
                causal_tags: list[str] | None = None) -> dict:
        authorized = capability in self.effective(agent_id) and capability in self.allowed
        event_type = "tool.executed" if authorized else "tool.denied"
        return self.log.append(
            event_type, agent_id,
            intent={"capability": capability}, input_data={"simulated": True},
            authorization={"allowed": authorized, "policy": "worldlab-only"},
            result={"executed": authorized, "external_side_effect": False},
            parent_event_ids=parent_event_ids,
            causal_tags=["simulated-tool-request", *(causal_tags or [])],
            evidence={"tool_hash": f"synthetic:{capability}"},
        )
