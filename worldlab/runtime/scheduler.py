"""Deterministic simulated-time scheduler for delayed WorldLab consequences."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Callable


@dataclass(order=True)
class ScheduledAction:
    at_minute: int
    order: int
    actor: str = field(compare=False)
    action: dict = field(compare=False)


class Scheduler:
    def __init__(self) -> None:
        self.now = 0
        self._order = 0
        self._queue: list[ScheduledAction] = []

    def schedule(self, delay_minutes: int, actor: str, action: dict) -> None:
        if delay_minutes < 0 or not actor or not isinstance(action, dict):
            raise ValueError("scheduled actions require a non-negative delay, actor and typed action")
        heapq.heappush(self._queue, ScheduledAction(self.now + delay_minutes, self._order, actor, action.copy()))
        self._order += 1

    def run(self, transition: Callable[[ScheduledAction], object], until_minute: int | None = None) -> list[object]:
        results = []
        while self._queue and (until_minute is None or self._queue[0].at_minute <= until_minute):
            scheduled = heapq.heappop(self._queue)
            self.now = scheduled.at_minute
            results.append(transition(scheduled))
        if until_minute is not None:
            self.now = max(self.now, until_minute)
        return results

    @property
    def pending(self) -> int:
        return len(self._queue)
