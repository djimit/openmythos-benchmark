"""Provider-neutral agent boundary and deterministic test agents."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable


@dataclass(frozen=True)
class WorldAgentAdapter:
    agent_id: str
    generate_fn: Callable[[dict], dict]
    provider: str = "synthetic"
    model: str = "deterministic"
    version: str = "1"

    def generate(self, context: dict) -> dict:
        started = perf_counter()
        try:
            response = self.generate_fn(context)
            return {"output": response, "invocation": {"provider": self.provider, "model": self.model,
                    "version": self.version, "latency_ms": round((perf_counter() - started) * 1000, 3),
                    "tokens": response.get("tokens"), "cost": response.get("cost"), "error": None, "retry": 0}}
        except Exception as error:
            return {"output": None, "invocation": {"provider": self.provider, "model": self.model,
                    "version": self.version, "latency_ms": round((perf_counter() - started) * 1000, 3),
                    "tokens": None, "cost": None, "error": type(error).__name__, "retry": 0}}

    def tool_request(self, capability: str) -> dict:
        return {"agent_id": self.agent_id, "capability": capability}

    def save_memory(self, memory_id: str, value: Any) -> dict:
        return {"agent_id": self.agent_id, "memory_id": memory_id, "value": value}

    def load_memory(self, memory_id: str) -> dict:
        return {"agent_id": self.agent_id, "memory_id": memory_id}


def _decision(kind: str) -> Callable[[dict], dict]:
    return lambda context: {"strategy": kind, "context_seen": sorted(context)}


def synthetic_agents() -> dict[str, WorldAgentAdapter]:
    """Strategies are deterministic; stochasticity belongs to the seeded environment."""
    return {
        name: WorldAgentAdapter(name, _decision(name))
        for name in (
            "AlwaysComplyAgent", "DelegatingAgent", "MaliciousAgent",
            "NoisyAgent", "IndependentChecker", "CorrelatedChecker",
        )
    }
