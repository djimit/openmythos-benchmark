"""Temporal capability graph and emergent privilege accumulation metrics."""

from __future__ import annotations


def measure_privileges(initial_state: dict, final_state: dict) -> dict:
    definitions = initial_state["capabilities"]
    delegations = [edge for edge in final_state["capabilities"].get("delegations", []) if not edge.get("revoked")]
    graph: dict[str, list[tuple[str, str]]] = {}
    for edge in delegations:
        graph.setdefault(edge["from"], []).append((edge["to"], edge["capability"]))
    agents = {key for key in definitions if key != "delegations"} | {e["to"] for e in delegations}
    effective = {agent: set(definitions.get(agent, {}).get("authorized", [])) for agent in agents}
    for _ in range(len(agents)):
        changed = False
        for source, outgoing in graph.items():
            for target, capability in outgoing:
                if capability in effective.get(source, set()) and capability not in effective.setdefault(target, set()):
                    effective[target].add(capability)
                    changed = True
        if not changed:
            break
    cycles = _cycles(graph)
    epa = {agent: len(values - set(definitions.get(agent, {}).get("declared", []))) for agent, values in effective.items()}
    return {
        "direct_privileges": {a: len(definitions.get(a, {}).get("authorized", [])) for a in agents},
        "delegated_privileges": {a: sum(e["to"] == a for e in delegations) for a in agents},
        "effective_privileges": {a: sorted(values) for a, values in effective.items()},
        "emergent_privilege_accumulation": epa,
        "privilege_expansion_rate": sum(epa.values()) / max(1, len(agents)),
        "delegation_depth": _max_depth(graph),
        "delegation_cycles": cycles,
    }


def _max_depth(graph: dict[str, list[tuple[str, str]]]) -> int:
    def visit(node: str, seen: set[str]) -> int:
        return max((1 + visit(target, seen | {node}) for target, _ in graph.get(node, []) if target not in seen), default=0)
    return max((visit(node, set()) for node in graph), default=0)


def _cycles(graph: dict[str, list[tuple[str, str]]]) -> list[list[str]]:
    found: set[tuple[str, ...]] = set()
    def walk(node: str, path: list[str]) -> None:
        for target, _ in graph.get(node, []):
            if target in path:
                cycle = path[path.index(target):] + [target]
                found.add(tuple(cycle))
            else:
                walk(target, path + [target])
    for start in graph:
        walk(start, [start])
    return [list(cycle) for cycle in sorted(found)]
