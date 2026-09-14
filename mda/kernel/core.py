"""Minimal Developmental Algorithm: frozen domain-independent kernel.

This module deliberately knows nothing about Andrews-Curtis.  Domain packs
supply grounding authority, protected replay, lawful continuations and cost
coordinates.

Canonical operation:
    retain exactly the differences whose erasure changes warranted future
    consequence.

The kernel therefore preserves UNKNOWN states and Pareto-incomparable lawful
continuations rather than forcing a scalar winner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class Status(str, Enum):
    VERIFIED = "VERIFIED"
    UNKNOWN_SEARCH = "UNKNOWN_SEARCH"
    UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"
    UNKNOWN_IDENTIFIABILITY = "UNKNOWN_IDENTIFIABILITY"
    UNKNOWN_CHOICE = "UNKNOWN_CHOICE"
    CERTIFIED_OBSTRUCTION = "CERTIFIED_OBSTRUCTION"
    SCOPE_FAILURE = "SCOPE_FAILURE"
    STALE_AUTHORITY = "STALE_AUTHORITY"


@dataclass(frozen=True)
class Warrant:
    status: Status
    scope: str
    authority_version: str
    reason: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Cost:
    """Named Pareto coordinates.

    Lower values are better unless a coordinate is explicitly placed in the
    candidate's maximize set.  Correctness/warrant are not cost coordinates;
    they are admission constraints and must be checked before this object is
    compared.
    """

    values: Mapping[str, float]


@dataclass(frozen=True)
class Candidate:
    id: str
    warrant: Warrant
    protected_replay_ok: bool
    cost: Cost
    maximize: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)


def lawful(c: Candidate) -> bool:
    return c.warrant.status is Status.VERIFIED and c.protected_replay_ok


def _value(c: Candidate, key: str) -> float:
    return float(c.cost.values.get(key, 0.0))


def dominates(a: Candidate, b: Candidate) -> bool:
    """Return True only when a is no worse in every declared coordinate.

    Candidates with different maximize declarations are intentionally not
    silently compared.  That is an UNKNOWN_CHOICE situation at the caller.
    """
    if not lawful(a) or not lawful(b):
        return False
    if a.maximize != b.maximize:
        return False
    keys = set(a.cost.values) | set(b.cost.values)
    no_worse = True
    strictly_better = False
    for key in keys:
        av, bv = _value(a, key), _value(b, key)
        if key in a.maximize:
            if av < bv:
                no_worse = False
                break
            if av > bv:
                strictly_better = True
        else:
            if av > bv:
                no_worse = False
                break
            if av < bv:
                strictly_better = True
    return no_worse and strictly_better


def pareto_frontier(candidates: Iterable[Candidate]) -> list[Candidate]:
    lawful_candidates = [c for c in candidates if lawful(c)]
    out: list[Candidate] = []
    for c in lawful_candidates:
        if any(d.id != c.id and dominates(d, c) for d in lawful_candidates):
            continue
        out.append(c)
    return sorted(out, key=lambda c: c.id)


def classify_search(*, complete: bool, adequate: bool) -> Status:
    if adequate:
        return Status.VERIFIED
    if not complete:
        return Status.UNKNOWN_SEARCH
    return Status.CERTIFIED_OBSTRUCTION


def classify_choice(frontier_size: int, discriminator_authorized: bool) -> Status:
    if frontier_size <= 1:
        return Status.VERIFIED
    if discriminator_authorized:
        # Authorization to probe is not evidence selecting a branch.
        return Status.UNKNOWN_CHOICE
    return Status.UNKNOWN_CHOICE


def transition_record(
    *,
    transition_id: str,
    from_present: str,
    encounter: str,
    observed_consequence: str,
    warrant: Warrant,
    residual: str,
    constraint: str,
    candidate_continuation: str,
    files_changed: Sequence[str],
    protected_replay: str,
    ablation: str,
    cost_before: Mapping[str, Any],
    cost_after: Mapping[str, Any],
    frontier_effect: str,
    retained: bool,
    reason: str,
    revocation_conditions: Sequence[str],
    to_present: str,
) -> dict[str, Any]:
    return {
        "transition_id": transition_id,
        "from_present": from_present,
        "encounter": encounter,
        "observed_consequence": observed_consequence,
        "warrant_status": warrant.status.value,
        "warrant_scope": warrant.scope,
        "authority_version": warrant.authority_version,
        "residual": residual,
        "constraint": constraint,
        "candidate_continuation": candidate_continuation,
        "files_changed": list(files_changed),
        "verification": {
            "status": warrant.status.value,
            "evidence": list(warrant.evidence),
        },
        "protected_replay": protected_replay,
        "ablation": ablation,
        "cost_before": dict(cost_before),
        "cost_after": dict(cost_after),
        "frontier_effect": frontier_effect,
        "retained": retained,
        "reason": reason,
        "revocation_conditions": list(revocation_conditions),
        "to_present": to_present,
    }
