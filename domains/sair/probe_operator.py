from __future__ import annotations

from typing import Any, Iterable, Mapping


def induce_numeric_literal_shift(domain, before, after, probe_id: str, record: Any) -> Iterable[Mapping[str, Any]]:
    """Induce a reusable integer-literal shift from a verified synthesized probe.

    No TRUE/FALSE answer is consulted. The operator is inferred only from the
    structural relation between the newly verified probe and an already available
    same-direction atomic probe in the prior epistemic language.
    """
    p = domain.programs.get(probe_id)
    if not p or p.get("kind") != "atom" or p.get("order") is None:
        return ()
    new_order = int(p["order"])
    direction = p.get("direction")
    parents = []
    for old_id in before.probe_language:
        old = domain.programs.get(old_id)
        if not old or old.get("kind") != "atom" or old.get("order") is None:
            continue
        if old.get("direction") != direction:
            continue
        delta = new_order - int(old["order"])
        if delta:
            parents.append((abs(delta), int(old["order"]), delta, old_id))
    if not parents:
        return ()
    _, old_order, delta, old_id = sorted(parents)[0]
    return ({
        "id": f"NUMERIC_LITERAL_SHIFT({delta:+d})",
        "kind": "NUMERIC_LITERAL_SHIFT",
        "delta": delta,
        "source_probe": old_id,
        "source_order": old_order,
        "verified_probe": probe_id,
        "verified_order": new_order,
        "cost": abs(delta) + 1,
    },)


def expand_numeric_literal_shift(domain, state, operator: Mapping[str, Any]) -> Iterable[str]:
    if operator.get("kind") != "NUMERIC_LITERAL_SHIFT":
        return ()
    delta = int(operator["delta"])
    out = []
    # Apply the learned operator to every atomic probe currently installed.
    # This permits recursive use: after 2->3 is learned, the same operator can
    # produce 3->4 without a named ORDER4/SUCC2 constructor.
    for probe_id in sorted(state.probe_language):
        p = domain.programs.get(probe_id)
        if not p or p.get("kind") != "atom" or p.get("order") is None:
            continue
        target_order = int(p["order"]) + delta
        direction = p.get("direction")
        for candidate_id, candidate in domain.programs.items():
            if candidate.get("kind") != "atom":
                continue
            if candidate.get("order") == target_order and candidate.get("direction") == direction:
                out.append(candidate_id)
    return tuple(sorted(set(out)))
