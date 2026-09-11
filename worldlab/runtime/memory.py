"""Attributed private/shared memory with explicit reads and corrections."""

from __future__ import annotations

from .event_log import EventLog
from .world_state import WorldState

SCOPES = {"private_episodic", "private_semantic", "shared", "artifact"}


class MemoryStore:
    def __init__(self, state: WorldState, log: EventLog) -> None:
        self.state = state
        self.log = log

    def write(self, author: str, memory_id: str, proposition: str, *, scope: str, confidence: float,
              provenance: list[str], parents: list[str] | None = None) -> dict:
        if not author or not provenance:
            raise ValueError("memory writes require author and provenance")
        if scope not in SCOPES:
            raise ValueError("memory scope is invalid")
        value = {
            "id": memory_id, "proposition": proposition, "scope": scope, "author": author,
            "origin": provenance[0], "confidence": confidence, "provenance": provenance,
            "parents": parents or [], "consumers": [], "corrected": False,
        }
        delta = {"set": [{"domain": "memory", "key": memory_id, "value": value}]}
        self.state.apply(delta)
        return self.log.append("memory.written", author, input_data={"memory_id": memory_id, "scope": scope},
                               result={"proposition": proposition}, state_delta=delta,
                               parent_event_ids=parents, causal_tags=["memory-provenance"],
                               evidence={"provenance": provenance, "confidence": confidence})

    def read(self, reader: str, memory_id: str) -> tuple[dict, dict]:
        memory = self.state.snapshot()["memory"].get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        if str(memory.get("scope", "")).startswith("private_") and memory.get("author") != reader:
            raise PermissionError("private memory access denied")
        updated = dict(memory)
        updated["consumers"] = [*updated.get("consumers", []), reader]
        delta = {"set": [{"domain": "memory", "key": memory_id, "value": updated}]}
        self.state.apply(delta)
        event = self.log.append("memory.read", reader, input_data={"memory_id": memory_id},
                                result={"found": True}, state_delta=delta,
                                parent_event_ids=memory.get("parents", []), causal_tags=["information-exposure"])
        return updated, event

    def correct(self, actor: str, memory_id: str, correction: str, parent_event_id: str) -> dict:
        memory = self.state.snapshot()["memory"].get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        updated = dict(memory)
        updated.update({"corrected": True, "correction": correction, "corrected_by": actor})
        delta = {"set": [{"domain": "memory", "key": memory_id, "value": updated}]}
        self.state.apply(delta)
        return self.log.append("memory.corrected", actor, input_data={"memory_id": memory_id},
                               result={"correction": correction}, state_delta=delta,
                               parent_event_ids=[parent_event_id], causal_tags=["recovery"])

    def message(self, sender: str, recipient: str, message_id: str, content_hash: str, provenance: list[str]) -> dict:
        if not sender or not recipient or not provenance or not content_hash:
            raise ValueError("messages require sender, recipient, hash and provenance")
        value = {"from": sender, "to": recipient, "content_hash": content_hash, "provenance": provenance}
        delta = {"append": [{"domain": "relationships", "key": "messages", "value": {"id": message_id, **value}}]}
        self.state.apply(delta)
        return self.log.append("agent.message", sender, input_data={"recipient": recipient, "message_id": message_id},
                               result={"content_hash": content_hash}, state_delta=delta,
                               causal_tags=["agent-communication"], evidence={"provenance": provenance})
