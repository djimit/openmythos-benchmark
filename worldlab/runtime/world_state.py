"""Controlled WorldLab state transitions."""

from __future__ import annotations

import copy

DOMAINS = (
    "agents", "memory", "capabilities", "relationships", "resources",
    "governance", "artifacts", "knowledge", "tasks",
)


def empty_state() -> dict:
    return {domain: {} for domain in DOMAINS}


class WorldState:
    def __init__(self, initial: dict | None = None) -> None:
        state = copy.deepcopy(initial or empty_state())
        if set(state) != set(DOMAINS) or not all(isinstance(state[d], dict) for d in DOMAINS):
            raise ValueError("world state must contain exactly the nine typed domains")
        self._state = state

    def snapshot(self) -> dict:
        return copy.deepcopy(self._state)

    def apply(self, delta: dict) -> None:
        """Apply the only supported mutations: typed set, append, and remove operations."""
        unknown = set(delta) - {"set", "append", "remove"}
        if unknown:
            raise ValueError(f"unknown state transition operations: {sorted(unknown)}")
        for item in delta.get("set", []):
            self._target(item)[item["key"]] = copy.deepcopy(item["value"])
        for item in delta.get("append", []):
            target = self._target(item).setdefault(item["key"], [])
            if not isinstance(target, list):
                raise ValueError("append target is not a list")
            target.append(copy.deepcopy(item["value"]))
        for item in delta.get("remove", []):
            self._target(item).pop(item["key"], None)

    def _target(self, item: dict) -> dict:
        domain = item.get("domain")
        key = item.get("key")
        if domain not in DOMAINS or not isinstance(key, str) or not key:
            raise ValueError("state transition needs a known domain and non-empty key")
        return self._state[domain]
