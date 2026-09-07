"""Append-only, hash-chained WorldLab event log."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class EventLog:
    """Creates immutable events whose order and content are tamper evident."""

    def __init__(self, experiment_id: str, trajectory_id: str, seed: int) -> None:
        self.experiment_id = experiment_id
        self.trajectory_id = trajectory_id
        self.seed = seed
        self._events: list[dict] = []
        self._epoch = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=seed)

    @property
    def events(self) -> list[dict]:
        return copy.deepcopy(self._events)

    def append(
        self,
        event_type: str,
        actor_id: str,
        *,
        actor_type: str = "agent",
        intent: dict | None = None,
        input_data: dict | None = None,
        authorization: dict | None = None,
        result: dict | None = None,
        state_delta: dict | None = None,
        parent_event_ids: list[str] | None = None,
        causal_tags: list[str] | None = None,
        evidence: dict | None = None,
    ) -> dict:
        sequence = len(self._events)
        timestamp = (self._epoch + timedelta(minutes=sequence)).isoformat()
        event_id = str(uuid5(NAMESPACE_URL, f"{self.trajectory_id}:{sequence}:{event_type}:{actor_id}"))
        previous_hash = self._events[-1]["event_hash"] if self._events else None
        event = {
            "event_id": event_id,
            "experiment_id": self.experiment_id,
            "trajectory_id": self.trajectory_id,
            "sequence": sequence,
            "timestamp_simulated": timestamp,
            "timestamp_wallclock": timestamp,
            "actor": {"type": actor_type, "id": actor_id},
            "event_type": event_type,
            "intent": intent or {},
            "input": input_data or {},
            "authorization": authorization or {},
            "result": result or {},
            "state_delta": state_delta or {},
            "parent_event_ids": parent_event_ids or [],
            "causal_tags": causal_tags or [],
            "evidence": evidence or {},
            "previous_hash": previous_hash,
        }
        event["event_hash"] = sha256(event)
        self._events.append(copy.deepcopy(event))
        return copy.deepcopy(event)

    @staticmethod
    def verify(events: list[dict]) -> None:
        previous_hash = None
        for sequence, event in enumerate(events):
            if event.get("sequence") != sequence or event.get("previous_hash") != previous_hash:
                raise ValueError(f"invalid event chain at sequence {sequence}")
            supplied_hash = event.get("event_hash")
            unsigned = {key: value for key, value in event.items() if key != "event_hash"}
            if supplied_hash != sha256(unsigned):
                raise ValueError(f"event content hash mismatch at sequence {sequence}")
            previous_hash = supplied_hash

    def write_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(canonical_json(event) + "\n" for event in self._events))
