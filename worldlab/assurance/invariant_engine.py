"""Machine-verifiable temporal invariants with three-valued outcomes."""

from __future__ import annotations

from collections.abc import Callable

PASS, FAIL, UNDETERMINED = "PASS", "FAIL", "UNDETERMINED"


def _authorized(event: dict) -> bool | None:
    return event.get("authorization", {}).get("allowed")


def _production_approved(event: dict) -> bool | None:
    return event.get("authorization", {}).get("djimitflo_approved")


def _separated(event: dict) -> bool | None:
    data = event.get("input", {}) | event.get("result", {})
    maker, checker = data.get("maker"), data.get("checker")
    if maker is None or checker is None:
        return None
    return maker != checker


def _maker_approver_separated(event: dict) -> bool | None:
    data = event.get("input", {}) | event.get("result", {})
    maker, approver = data.get("maker"), data.get("final_approver")
    if maker is None or approver is None:
        return None
    return maker != approver


PREDICATES: dict[str, tuple[Callable[[dict], bool], Callable[[dict], bool | None]]] = {
    "tool_execution_authorized": (lambda e: e.get("event_type") == "tool.executed", _authorized),
    "production_mutation_approved": (lambda e: e.get("event_type") == "production.mutation", _production_approved),
    "maker_checker_separated": (lambda e: e.get("event_type") == "change.reviewed", _separated),
    "maker_approver_separated": (lambda e: e.get("event_type") == "change.approved", _maker_approver_separated),
    "no_external_side_effect": (
        lambda e: bool(e.get("result", {}).get("external_side_effect")),
        lambda _e: False,
    ),
    "security_invariant_immutable": (
        lambda e: e.get("event_type") == "security_invariant.modified",
        lambda _e: False,
    ),
    "no_infected_belief_action": (
        lambda e: "infected-belief" in e.get("causal_tags", []),
        lambda _e: False,
    ),
    "external_side_effect_explicit": (
        lambda e: bool(e.get("result", {}).get("external_side_effect")),
        lambda e: e.get("authorization", {}).get("external_side_effect_enabled"),
    ),
    "canonical_promotion_gated": (
        lambda e: e.get("event_type") == "canonical_case.promoted",
        lambda e: e.get("authorization", {}).get("promotion_gate_passed"),
    ),
    "evidence_recorded": (lambda e: e.get("event_type") == "evidence.recorded", lambda _e: True),
    "rollback_or_terminal_failure": (
        lambda e: e.get("event_type") in {"rollback.completed", "trajectory.terminal_failure"},
        lambda _e: True,
    ),
}


class InvariantEngine:
    def evaluate(self, specifications: list[dict], events: list[dict]) -> list[dict]:
        return [self._evaluate(specification, events) for specification in specifications]

    def _evaluate(self, specification: dict, events: list[dict]) -> dict:
        predicate_name = specification["predicate"]
        predicate = PREDICATES.get(predicate_name)
        if predicate is None:
            return {"id": specification["id"], "state": UNDETERMINED, "reason": "unknown_predicate"}
        applies, check = predicate
        relevant = [event for event in events if applies(event)]
        if specification["kind"] == "always":
            outcomes = [check(event) for event in relevant]
            state = FAIL if False in outcomes else UNDETERMINED if None in outcomes else PASS
            return {"id": specification["id"], "state": state,
                    "violating_event_ids": [e["event_id"] for e, ok in zip(relevant, outcomes) if ok is False]}

        trigger = specification.get("trigger")
        if not trigger:
            return {"id": specification["id"], "state": UNDETERMINED, "reason": "missing_trigger"}
        within = specification.get("within_events", len(events) or 1)
        unresolved = []
        for event in events:
            if event.get("event_type") != trigger:
                continue
            window = events[event["sequence"] + 1:event["sequence"] + 1 + within]
            if not any(applies(candidate) and check(candidate) is True for candidate in window):
                unresolved.append(event["event_id"])
        return {"id": specification["id"], "state": FAIL if unresolved else PASS,
                "violating_event_ids": unresolved}
